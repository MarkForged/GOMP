from subprocess import run
import unittest


class GOMPIntegrationTestCase(unittest.TestCase):

    maxDiff = None

    def setUp(self):
        run(['sh', 'setUp.sh'])

    def tearDown(self):
        run(['sh', 'tearDown.sh'])

    def test_feature_main(self):
        gomp_output = run(['python3', '../gomp.py', 'feature', 'main'],
                          capture_output=True,
                          universal_newlines=True,
                          check=False,
                          ).stdout
        f = open('expected_output/feature_main.txt', 'r')
        expected_output = f.read()
        f.close()
        self.assertEqual(gomp_output, expected_output)

    def test_recut_feature_main(self):
        gomp_output = run(['python3', '../gomp.py', 'feature', 'main', '--recut'],
                          capture_output=True,
                          universal_newlines=True,
                          check=False,
                          ).stdout
        f = open('expected_output/recut_feature_main.txt', 'r')
        expected_output = f.read()
        f.close()
        self.assertEqual(gomp_output, expected_output)

    def test_key_feature_main(self):
        gomp_output = run(['python3', '../gomp.py', 'feature', 'main', '--key'],
                          capture_output=True,
                          universal_newlines=True,
                          check=False,
                          ).stdout
        f = open('expected_output/key_feature_main.txt', 'r')
        expected_output = f.read()
        f.close()
        self.assertEqual(gomp_output, expected_output)

    def test_help(self):
        gomp_output = run(['python3', '../gomp.py', '-h'],
                          capture_output=True,
                          universal_newlines=True,
                          check=False,
                          ).stdout
        f = open('expected_output/help.txt', 'r')
        expected_output = f.read()
        f.close()
        self.assertEqual(gomp_output, expected_output)

if __name__ == '__main__':
    unittest.main()
