#!usr/bin/env python

# Side by side branch diffing from last common hash:
#     gomp staging rc
# Show color code:
#     gomp staging rc --key
# Recut staging using rc as base. Output is ready for interactive rebase:
#     gomp staging rc --recut

# Assumes that the source is the current branch of none is specified
#     git checkout main
#     gomp feature-branch
# equivalent to:
#     gomp main feature-branch

import os
import re
from subprocess import run, PIPE
import argparse

#############
### ENUMS ###
#############

# pylint: disable=global-statement
class Commands:
    show_side_by_side = 'show side by side'
    offset_recut = 'offer recut'


class BColors:
    # pylint: disable=invalid-name
    WHITE = '\033[37m'
    HEADER = '\033[95m'
    COMMON = '\033[92m'
    SRC_NEW = '\033[95m'
    DEST_NEW = '\033[91m'
    SIMILAR = '\033[93m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ENDC = '\033[0m'


######################
### HELPER METHODS ###
######################


def colorize(text, color):
    return color + text + BColors.ENDC


# Converts text-only history to (hash, title) tuples
def process_history(hist):
    # pylint: disable=consider-using-enumerate
    for i in range(len(hist)):
        _hash = hist[i][0:40]
        _title = hist[i][41:]
        hist[i] = [_hash, _title]
    return hist


def format_lint(line, width=0):
    text = line[0]
    color = BColors.WHITE
    if len(line) == 2:
        color = line[1]
    return colorize(fix_text_length(text, width), color)


def fix_text_length(text, width=0):
    if width == 0:
        width = int(line_length / 2 - 1)
    return ('{:<' + str(width) + '}').format(text[:width])


# Display color key
def print_color_key(source='src', destination='dest'):
    print(colorize('Common commit', BColors.COMMON))
    print(colorize('Similar commit', BColors.SIMILAR))
    print(colorize('Unique {} commit'.format(source), BColors.SRC_NEW))
    print(colorize('Unique {} commit'.format(destination), BColors.DEST_NEW))
    print('')


hash_length = 7
line_length = 80
branch_name_length = 10
src = None
dest = None
source_history = None
destination_history = None

#####################
### HEAVY LIFITNG ###
#####################


def create_title_map(commits, end_hash=None):
    title_map = {}
    # Note: we must compute the entire history of commit name-mapping here
    # to account for highly divergent branches. This could maybe be more clever.
    for commit in commits:
        # If there are conflicting titles, suffix them with hash
        if commit[1] in title_map:
            commit[1] = commit[1] + ' - ' + commit[0][0:hash_length]
        # Map titles to hashes
        title_map[commit[1]] = commit[0]
    return title_map


# Finds the first common hash between two histories
def find_first_common_hash(source_commit, destination_commit, previous=0):
    source_map = {}
    destination_map = {}

    index = 0
    while True:
        source_in_bound = index < len(source_commit)
        dest_in_bound = index < len(destination_commit)

        if source_in_bound:
            hash_source = source_commit[index][0]
            source_map[hash_source] = True

        if dest_in_bound:
            hash_dest = destination_commit[index][0]
            destination_map[hash_dest] = True

        # Are we out of runway?
        if not (source_in_bound or dest_in_bound):
            raise Exception('The branches share no common history!')

        # If either hash is present in the other branch by now, success!
        if dest_in_bound and hash_dest in source_map:
            return hash_dest
        if source_in_bound and hash_source in destination_map:
            return hash_source
        index += 1


# Returns a list of hash + title paired with color code
def construct_diff_list(
    commits, source_title_map, destination_title_map, end_hash
):
    i = 0
    trailing_rows = 5
    count_down_trailing_rows = False
    rows = []
    # Print until matching hash found
    while trailing_rows > 0:
        row = commits[i]
        _hash = row[0]
        _title = row[1]
        exists_in_source = _title in source_title_map
        exists_in_destination = _title in destination_title_map
        exists_in_both = exists_in_source and exists_in_destination
        same_commit = (
            exists_in_both
            and source_title_map[_title] == destination_title_map[_title]
        )

        # Color code outputs based on existence in branches
        if same_commit:
            rows.append([_hash[0:hash_length] + ' ' + _title, BColors.COMMON])
        elif exists_in_both:
            rows.append([_hash[0:hash_length] + ' ' + _title, BColors.SIMILAR])
        elif exists_in_destination:
            rows.append([_hash[0:hash_length] + ' ' + _title, BColors.DEST_NEW])
        elif exists_in_source:
            rows.append([_hash[0:hash_length] + ' ' + _title, BColors.SRC_NEW])
        else:
            raise Exception('https://xkcd.com/2200/')

        # If there are no more commits, we're done
        i += 1
        if i >= len(commits):
            break

        # If the target hash is found, start a countdown of trailing context commits.
        if _hash == end_hash:
            count_down_trailing_rows = True
        elif count_down_trailing_rows:
            trailing_rows -= 1

    return rows


# Print the history side by side until (and including) the given hash
def compute_side_by_side(commits_source, commits_destination, _hash):
    # Compute the existing commits and title elements
    source_title_map = create_title_map(commits_source, _hash)
    destination_title_map = create_title_map(commits_destination, _hash)
    # Pretty-print the two histories side by side (common hashes aligned)
    source_diff_list = construct_diff_list(
        commits_source, source_title_map, destination_title_map, _hash
    )
    destination_diff_list = construct_diff_list(
        commits_destination, source_title_map, destination_title_map, _hash
    )
    source_length = len(source_diff_list)
    destination_length = len(destination_diff_list)
    source_offset = max(destination_length - source_length, 0)
    destination_offset = max(source_length - destination_length, 0)
    side_by_side = []
    i = 0
    while i < max(source_length, destination_length):
        left_text = format_lint([''])
        right_text = format_lint([''])
        if i - source_offset >= 0:
            left_text = format_lint(source_diff_list[i - source_offset])
        if i - destination_offset >= 0:
            right_text = format_lint(
                destination_diff_list[i - destination_offset]
            )
        i += 1
        side_by_side.append(left_text + '  ' + right_text)
    return side_by_side


# Print the recut offer given a common hash
def compute_recut_offer(commits_source, commits_destination, _hash):
    res = []
    # Compute the existing commits and title elements
    source_title_map = create_title_map(commits_source, _hash)
    destination_title_map = create_title_map(commits_destination, _hash)
    # Take all of the src-only commits and cut them on top of dest's stem
    source_diff_list = construct_diff_list(
        commits_source, source_title_map, destination_title_map, _hash
    )
    for line in source_diff_list:
        if line[1] == BColors.SRC_NEW:
            res.append(line)
    # Use the destination branch as the stem (unchanged)
    destination_diff_list = construct_diff_list(
        commits_destination, source_title_map, destination_title_map, _hash
    )
    for line in destination_diff_list:
        res.append(line)
    return res


# Print lines in reverse order so they are copy-paste ready for interactive rebase
def print_for_rebase(lines):
    lines = lines[:]
    lines.reverse()
    lines = [['pick ' + line[0], line[1]] for line in lines]
    widest = len(max(lines, key=lambda line: len(line[0]))[0])
    prefix = ' # Only on '
    extras_length = len(prefix) + branch_name_length
    if widest < line_length - extras_length:
        width = widest
    else:
        width = line_length - extras_length
    for line in lines:
        extras = ''
        if line[1] == BColors.DEST_NEW:
            extras = colorize(
                prefix
                + '{}'.format(fix_text_length(dest, width=branch_name_length)),
                BColors.WHITE,
            )
        print(format_lint(line, width=width) + extras)


# Show relevant history side by side
def show_side_by_side():
    global hash_length, line_length
    hash_length = 7
    source_branch = fix_text_length(src + ' (src)')
    destination_branch = fix_text_length(dest + ' (dest)')
    print(
        format_lint([source_branch, BColors.BOLD])
        + '  '
        + format_lint([destination_branch, BColors.BOLD])
    )
    print(
        format_lint([re.sub(r'.', '-', source_branch), BColors.BOLD])
        + '  '
        + format_lint([re.sub(r'.', '-', destination_branch), BColors.BOLD])
    )
    common_hash = find_first_common_hash(source_history, destination_history, 4)
    lines = compute_side_by_side(
        source_history, destination_history, common_hash
    )
    for line in lines:
        print(line)


# Show recut proposal
def show_recut_offer():
    global hash_length, line_length
    hash_length = 16
    title_text = 'Recut {} from {}'.format(src, dest)
    title = fix_text_length(title_text)
    _title = format_lint([title, BColors.BOLD])
    print(_title)
    print((format_lint([re.sub(r'.', '-', title), BColors.BOLD])))
    common_hash = find_first_common_hash(source_history, destination_history, 4)
    lines = compute_recut_offer(
        source_history, destination_history, common_hash
    )
    print_for_rebase(lines)


def branch_exists(branch):
    verify = run(
        ['git', 'cat-file', '-t', branch],
        stdout=PIPE,
        universal_newlines=True,
        check=False,
    ).stdout.strip()
    return verify == 'commit'


# Basic command input parser
def process_commands():
    global src, dest, source_history, destination_history, line_length

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'src', nargs='?', default='HEAD', help='Left side branch'
    )
    parser.add_argument('dest', help='Right side branch')
    parser.add_argument(
        '--key', help='Display with color code', action='store_true'
    )
    parser.add_argument('--recut', help='Recut view', action='store_true')
    parser.add_argument('--cols', help='Number of columns')
    args = parser.parse_args()

    src = args.src
    dest = args.dest

    if not branch_exists(src):
        print('Branch {} does not exist'.format(colorize(src, BColors.SRC_NEW)))

    if not branch_exists(dest):
        print(
            'Branch {} does not exist'.format(colorize(dest, BColors.DEST_NEW))
        )

    # Check if src and dest exist
    if not (branch_exists(src) and branch_exists(dest)):
        print(
            'Local may not be synced with remote, please run {} and try again'.format(
                colorize('git fetch', BColors.COMMON)
            )
        )
        print('')
        return

    # Grab inline history of both branches
    source_history = run(
        ['git', '--no-pager', 'log', src, '--pretty=oneline'],
        stdout=PIPE,
        universal_newlines=True,
        check=False,
    ).stdout.splitlines()
    destination_history = run(
        ['git', '--no-pager', 'log', dest, '--pretty=oneline'],
        stdout=PIPE,
        universal_newlines=True,
        check=False,
    ).stdout.splitlines()
    source_history = process_history(source_history)
    destination_history = process_history(destination_history)

    print('')
    cmd = Commands.show_side_by_side
    # Display with color code
    if args.key:
        print_color_key(src, dest)
    # Display with color code
    if args.recut:
        cmd = Commands.offset_recut
    # Configure the number of columns
    if args.cols != None:
        line_length = int(args.cols)
    else:
        line_length = int(os.get_terminal_size().columns)
    # Run the proper command
    if cmd == Commands.show_side_by_side:
        show_side_by_side()
    elif cmd == Commands.offset_recut:
        show_recut_offer()
    print('')


if __name__ == '__main__':
    process_commands()
