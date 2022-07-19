#!/bin/bash

#
# release.bash - Sets the version to the one given in next_version file
#

NEXT_VERSION=$(cat next_version)
bump2version build --tag --commit --new-version $NEXT_VERSION
