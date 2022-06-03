#!/bin/bash
#
# check.bash - Checks Darcy AI development environment prerequisites
#

# Check python version
function check_python_version() {

    if ! python3 -c 'import sys; assert sys.version_info >= (3,6,9)' > /dev/null 2>&1; then
        printf "\t\t\xE2\x9C\x98 Ensure Python is 3.6.9 or later\n"
        return 1
    else
        printf "\t\t\xE2\x9C\x93 Ensure Python is 3.6.9 or later\n"
        return 0
    fi

}

# Check OpenCV version
function check_opencv_version() {

    if ! python3 -c 'import cv2; assert cv2.__version__ >= "3.4.17.63"' > /dev/null 2>&1; then
        printf "\t\t\xE2\x9C\x98 Ensure OpenCV is 3.4.17.63 or later\n"
        return 1
    else
        printf "\t\t\xE2\x9C\x93 Ensure OpenCV is 3.4.17.63 or later\n"
        return 0
    fi

}

# Check python package installed
function check_python_package() {

    if ! python3 -c "import $1" > /dev/null 2>&1; then
        printf "\t\xE2\x9C\x98 Checking Python package '$1'\n"
        return 1
    else
        printf "\t\xE2\x9C\x93 Checking Python package '$1'\n"
        return 0
    fi

}

# Check command exists
function check_command_exists() {

    if ! command -v $1 > /dev/null 2>&1; then
        printf "\t\xE2\x9C\x98 Checking $1\n"
        return 1
    else
        printf "\t\xE2\x9C\x93 Checking $1\n"
        return 0
    fi

}

printf "Checking tools\n"
check_command_exists docker

check_command_exists python3
check_python_version

printf "\nChecking Python packages\n"

if check_python_package cv2; then
    check_opencv_version
fi

check_python_package pycoral
check_python_package darcyai
