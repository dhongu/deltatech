#!/bin/sh

module=$1

git checkout -b 17.0-mig-$module
git format-patch --keep-subject --stdout origin/17.0..origin/16.0 -- $module | git am -3 --keep
pre-commit run -a  # to run black, isort and prettier (ignore pylint errors at this stage)
git add -A
git commit -m "[IMP] $module: pre-commit stuff"  --no-verify  # it is important to do all formatting in one commit the first time


# git am --abort  # if something goes wrong
