#!/bin/bash
#
# bump_version.bash [NEW_VERSION] - Bumps the batch part of the version number or sets it to the given NEW_VERSION
#

if [[ -z $1 ]]; then
  bump2version patch src/darcyai/__init__.py --tag --commit
else
  bump2version patch src/darcyai/__init__.py --tag --commit --new-version $1
fi
