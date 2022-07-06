#!/bin/bash
#
# release.bash - Reads the version number from next_version file and changes the version number in all relevant files.
#

NEXT_VERSION=$(cat ./next_version)
bump2version patch src/darcyai/__init__.py --tag --commit --new-version $NEXT_VERSION
echo "Tagged version v$NEXT_VERSION, remember to increment ./next_version"