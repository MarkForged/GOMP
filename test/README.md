# GOMP Tests

GOMP features automated testing to protect against bugs and regressions. To run the tests, use:

```bash
$ python test.py
```

This will run tests on the output of GOMP, which verify that the tool is returning the correct output on a standardized Git history.

### How it Works

The folder "test-history" was created with `create_git_history.sh`. This script creates a complex Git history that expresses all possible combinations of commits that GOMP is designed to handle (as enumerated with the --key flag). Because Git creates hashes that change based on the timestamp, rather than creating this Git history from scratch every time we run the test, we simply move it to ".git" so that it acts as a Git history that the tests can run against. If the history were re-created every time, tests would fail as the commit hashes would not match between the output and the expected output files in the folder "expected_output."

