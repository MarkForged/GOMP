from subprocess import run, PIPE
import unittest

# The number of columns to use during test recording and playback
NUM_COLS = '80'

class GOMPIntegrationTestCase(unittest.TestCase):

    maxDiff = None

    def setUp(self):
        run(['sh', 'setUp.sh'])

    def tearDown(self):
        run(['sh', 'tearDown.sh'])

    def test_feature_main(self):
        gomp_output = run(['python3', '../gomp.py', 'feature', 'main', '--cols', NUM_COLS],
                          stdout=PIPE,
                          universal_newlines=True,
                          check=False,
                          ).stdout
        f = open('expected_output/feature_main.txt', 'r')
        expected_output = f.read()
        f.close()
        self.assertEqual(gomp_output, expected_output)

    def test_recut_feature_main(self):
        gomp_output = run(['python3', '../gomp.py', 'feature', 'main', '--recut', '--cols', NUM_COLS],
                          stdout=PIPE,
                          universal_newlines=True,
                          check=False,
                          ).stdout
        f = open('expected_output/recut_feature_main.txt', 'r')
        expected_output = f.read()
        f.close()
        self.assertEqual(gomp_output, expected_output)

    def test_key_feature_main(self):
        gomp_output = run(['python3', '../gomp.py', 'feature', 'main', '--key', '--cols', NUM_COLS],
                          stdout=PIPE,
                          universal_newlines=True,
                          check=False,
                          ).stdout
        f = open('expected_output/key_feature_main.txt', 'r')
        expected_output = f.read()
        f.close()
        self.assertEqual(gomp_output, expected_output)

    def test_hash_vs_ref(self):
        gomp_output = run(['python3', '../gomp.py', 'feature~2', '5950d06', '--cols', NUM_COLS],
                          stdout=PIPE,
                          universal_newlines=True,
                          check=False,
                          ).stdout
        f = open('expected_output/hash_vs_ref.txt', 'r')
        expected_output = f.read()
        f.close()
        self.assertEqual(gomp_output, expected_output)

    def test_merge_multiple_commits(self):
        gomp_output = run(['python3', '../gomp.py', 'main-merge-target', 'main-merge-target~1', '--cols', NUM_COLS],
                          stdout=PIPE,
                          universal_newlines=True,
                          check=False,
                          ).stdout
        f = open('expected_output/merge_multiple_commits.txt', 'r')
        expected_output = f.read()
        f.close()
        self.assertEqual(gomp_output, expected_output)

    def test_help(self):
        gomp_output = run(['python3', '../gomp.py', '-h'],
                          stdout=PIPE,
                          universal_newlines=True,
                          check=False,
                          ).stdout
        f = open('expected_output/help.txt', 'r')
        expected_output = f.read()
        f.close()
        self.assertEqual(gomp_output, expected_output)

if __name__ == '__main__':
    unittest.main()
