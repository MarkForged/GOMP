#!/bin/bash

function fakecommit {
    touch $1.temp
    git add .
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
mv .git test_history
rm *.temp