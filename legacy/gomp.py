#!/usr/bin/env python
# Side by side branch diffing from last common hash:
#   gomp staging rc
# Show color code:
#   gomp staging rc --key
# Recut staging using rc as base. Output is ready for interactive rebase:
#   gomp staging rc --recut

# Assumes that the source is the current branch of none is specified
#   git checkout master
#   gomp feature-branch
# equivalent to:
#   gomp master feature-branch

import sys, os
import re
from subprocess import check_output, CalledProcessError
import argparse

#############
### ENUMS ###
#############


class commands:
    SHOW_SIDE_BY_SIDE = "show side by side"
    OFFER_RECUT = "offer recut"


class bcolors:
    WHITE = "\033[37m"
    HEADER = "\033[95m"
    COMMON = "\033[92m"
    SRC_NEW = "\033[95m"
    DEST_NEW = "\033[91m"
    SIMILAR = "\033[93m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    ENDC = "\033[0m"


######################
### HELPER METHODS ###
######################


def colorize(text, color):
    return color + text + bcolors.ENDC


# Converts text-only history to (hash, title) tuples
def process_history(hist):
    for i in xrange(len(hist)):
        _hash = hist[i][0:40]
        _title = hist[i][41:]
        hist[i] = [_hash, _title]
    return hist


def format_line(line, width=0):
    text = line[0]
    color = bcolors.WHITE
    if len(line) == 2:
        color = line[1]
    return colorize(fix_text_length(text, width), color)


def fix_text_length(text, width=0):
    if width == 0:
        width = LINE_LENGTH / 2 - 1
    return ("{:<" + str(width) + "}").format(text[:(width)])


HASH_LENGTH = 7
REBASE_FORMAT = False
NUM_LINES, LINE_LENGTH = os.popen("stty size", "r").read().split()
LINE_LENGTH = int(LINE_LENGTH)
BRANCH_NAME_LENGTH = 10

#####################
### HEAVY LIFITNG ###
#####################


def create_title_map(A, endHash=None):
    title_map = {}
    for a in A:
        # If there are conflicting titles, suffix them with hash
        if a[1] in title_map:
            a[1] = a[1] + " - " + a[0][0:HASH_LENGTH]
        # Map titles to hashes
        title_map[a[1]] = a[0]
        if a[0] == endHash:
            break
    return title_map


# Finds the first common hash between two histories
def find_first_common_hash(a, b, previous=0):
    Amap = {}
    Bmap = {}
    _hash = "?"
    # Find first common hash occurence
    for i in xrange(min(len(a), len(b))):
        hashA = a[i][0]
        hashB = b[i][0]
        Amap[hashA] = i
        Bmap[hashB] = i
        if hashA in Bmap:
            _hash = a[i][0]
            break
        if hashB in Amap:
            _hash = b[i][0]
            break
    # Traverse either history to find that hash and select 'previous' hashes ago
    i = 0
    while True:
        if a[i][0] == _hash:
            break
        i += 1
    # min here avoids out of bounds error in short repos
    i += min(previous, len(a) - i - 1)
    return a[i][0]


# Returns a list of hash + title paired with color code
def construct_diff_list(ls, title_map_A, title_map_B, endHash):
    done = False
    i = 0
    rows = []
    # Print until matching hash found
    while not done:
        row = ls[i]
        _hash = row[0]
        _title = row[1]
        exist_in_A = _title in title_map_A
        exist_in_B = _title in title_map_B
        exist_both = exist_in_A and exist_in_B
        sameCommit = exist_both and title_map_A[_title] == title_map_B[_title]

        # Color code outputs based on existence in branches
        if sameCommit:
            rows.append([_hash[0:HASH_LENGTH] + " " + _title, bcolors.COMMON])
        elif exist_both:
            rows.append([_hash[0:HASH_LENGTH] + " " + _title, bcolors.SIMILAR])
        elif exist_in_B:
            rows.append([_hash[0:HASH_LENGTH] + " " + _title, bcolors.DEST_NEW])
        elif exist_in_A:
            rows.append([_hash[0:HASH_LENGTH] + " " + _title, bcolors.SRC_NEW])
        i += 1
        if _hash == endHash:
            done = True
    return rows


# Print the history side by side until (and including) the given hash
def compute_side_by_side(A, B, _hash):
    # Compute the existing commits and title elements
    title_map_A = create_title_map(A, _hash)
    title_map_B = create_title_map(B, _hash)
    # Pretty-print the two histories side by side (common hashes aligned)
    LA = construct_diff_list(A, title_map_A, title_map_B, _hash)
    LB = construct_diff_list(B, title_map_A, title_map_B, _hash)
    NA = len(LA)
    NB = len(LB)
    offsetA = max(NB - NA, 0)
    offsetB = max(NA - NB, 0)
    sideBySide = []
    i = 0
    while i < max(NA, NB):
        leftText = format_line([""])
        rightText = format_line([""])
        if i - offsetA >= 0:
            leftText = format_line(LA[i - offsetA])
        if i - offsetB >= 0:
            rightText = format_line(LB[i - offsetB])
        i += 1
        sideBySide.append(leftText + "  " + rightText)
    return sideBySide


# Print the recut offer given a common hash
def compute_recut_offer(A, B, _hash):
    res = []
    # Compute the existing commits and title elements
    title_map_A = create_title_map(A, _hash)
    title_map_B = create_title_map(B, _hash)
    # Take all of the src-only commits and cut them on top of dest's stem
    LA = construct_diff_list(A, title_map_A, title_map_B, _hash)
    for line in LA:
        if line[1] == bcolors.SRC_NEW:
            res.append(line)
    # Use the destination branch as the stem (unchanged)
    LB = construct_diff_list(B, title_map_A, title_map_B, _hash)
    for line in LB:
        res.append(line)
    return res


# Print lines in reverse order so they are copy-paste ready for interactive rebase
def print_for_rebase(lines):
    lines = lines[:]
    lines.reverse()
    lines = map(lambda line: ["pick " + line[0], line[1]], lines)
    widest = len(max(lines, key=lambda line: len(line[0]))[0])
    prefix = " # Only on "
    extrasLength = len(prefix) + BRANCH_NAME_LENGTH
    if widest < LINE_LENGTH - extrasLength:
        width = widest
    else:
        width = LINE_LENGTH - extrasLength
    for line in lines:
        extras = ""
        if line[1] == bcolors.DEST_NEW:
            extras = colorize(
                prefix
                + "{}".format(fix_text_length(dest, width=BRANCH_NAME_LENGTH)),
                bcolors.WHITE,
            )
        print format_line(line, width=width) + extras
    return


# Display color code
def print_color_code(src="src", dest="dest"):
    print colorize("Common commit", bcolors.COMMON)
    print colorize("Similar commit", bcolors.SIMILAR)
    print colorize("Unique {} commit".format(src), bcolors.SRC_NEW)
    print colorize("Unique {} commit".format(dest), bcolors.DEST_NEW)
    print ""
    return


# Show relevant history side by side
def show_side_by_side():
    global HASH_LENGTH, REBASE_FORMAT, LINE_LENGTH
    HASH_LENGTH = 7
    REBASE_FORMAT = False
    branchA = fix_text_length(src + " (src)")
    branchB = fix_text_length(dest + " (dest)")
    print (
        format_line([branchA, bcolors.BOLD])
        + "  "
        + format_line([branchB, bcolors.BOLD])
    )
    print (
        format_line([re.sub(r".", "-", branchA), bcolors.BOLD])
        + "  "
        + format_line([re.sub(r".", "-", branchB), bcolors.BOLD])
    )
    commonHash = find_first_common_hash(src_history, dest_history, 4)
    lines = compute_side_by_side(src_history, dest_history, commonHash)
    for line in lines:
        print line
    return


# Show recut proposal
def show_recut_offer():
    global HASH_LENGTH, REBASE_FORMAT, LINE_LENGTH
    HASH_LENGTH = 16
    REBASE_FORMAT = True
    titleText = "Recut {} from {}".format(src, dest)
    title = fix_text_length(titleText)
    _title = format_line([title, bcolors.BOLD])
    print _title
    print format_line([re.sub(r".", "-", title), bcolors.BOLD])
    commonHash = find_first_common_hash(src_history, dest_history, 4)
    lines = compute_recut_offer(src_history, dest_history, commonHash)
    print_for_rebase(lines)
    return


def current_branch():
    return check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()


def branch_exists(branch, output=True):
    try:
        check_output(["git", "show-ref", branch])
        return True
    except CalledProcessError:
        if output:
            print (
                "{} does not exist".format(colorize(branch, bcolors.DEST_NEW))
            )
        return False


# Basic command input parser
def processCommands():
    global src, dest, src_history, dest_history

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "src", nargs="?", default="HEAD", help="Left side branch"
    )
    parser.add_argument("dest", help="Right side branch")
    parser.add_argument(
        "--key", help="Display with color code", action="store_true"
    )
    parser.add_argument("--recut", help="Recut view", action="store_true")
    args = parser.parse_args()

    src = args.src
    dest = args.dest

    # Check if src and dest exist
    if not (branch_exists(src) and branch_exists(dest)):
        fetch_colored = colorize("git fetch", bcolors.COMMON)
        print "Local may not be synced with remote, please run {} and try again".format(
            colorize("git fetch", bcolors.COMMON)
        )
        print ""
        return

    # Grab inline history of both branches
    src_history = check_output(
        ["git", "--no-pager", "log", src, "--pretty=oneline"]
    )
    dest_history = check_output(
        ["git", "--no-pager", "log", dest, "--pretty=oneline"]
    )
    src_history = process_history(src_history.split("\n"))
    dest_history = process_history(dest_history.split("\n"))

    print ""
    cmd = commands.SHOW_SIDE_BY_SIDE
    # Display with color code
    if args.key:
        print_color_code(src, dest)
    # Display with color code
    if args.recut:
        cmd = commands.OFFER_RECUT
    # Run the proper command
    if cmd == commands.SHOW_SIDE_BY_SIDE:
        show_side_by_side()
    elif cmd == commands.OFFER_RECUT:
        show_recut_offer()
    print ""
    return


if __name__ == "__main__":
    processCommands()
