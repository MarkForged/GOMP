#!/bin/bash

function fakecommit {
    touch $1.temp
    git add *.temp
    git commit -m "Commit $1"
}

git init
git checkout -b main
git branch -D master
fakecommit 0
fakecommit 1
fakecommit 2
git checkout -b feature
fakecommit a
fakecommit b
git checkout main
fakecommit I
fakecommit II
fakecommit 3
git checkout feature
git cherry-pick main@{0}
fakecommit c
git checkout main
fakecommit III
fakecommit IV
fakecommit 4
git checkout feature
git cherry-pick main@{0}
fakecommit d
git checkout main
fakecommit V
fakecommit VI

git checkout -b main-merge-target
git checkout -b main-forked
fakecommit e1
fakecommit e2
fakecommit e3
fakecommit e4
fakecommit e5
fakecommit e6
git checkout main-merge-target
fakecommit m1
fakecommit m2
fakecommit m3
git merge main-forked

mv .git test_history
rm *.temp
