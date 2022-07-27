#!/usr/bin/env bash -l

#
# setup_darcyai_m1.bash - is a utlility script that will create a new Conda environment
# and install all of the required libraries needed by DarcyAI to be able to run successfully
# on one of the newer Apple M1 MacOS platforms.
#

set -e

# This is the list of colors used in our messages
NO_FORMAT="\\033[0m"
C_SKYBLUE1="\\033[38;5;117m"
C_DEEPSKYBLUE4="\\033[48;5;25m"
RED="\\033[38;5;1m"
GREEN="\\033[38;5;28m"

# Need this as bash and sh require different args for the echo command
if [ "${BASH_VERSION}" ]; then
    PRINTARGS="-e"
fi

# Basic subtle output
echoInfo() {
  echo ${PRINTARGS} "${C_SKYBLUE1}$1 ${NO_FORMAT}"
}

echoSuccess() {
  echo ${PRINTARGS} "${GREEN}$1 ${NO_FORMAT}"
}

# Highlighted output with a background
echoNotify() {
  echo ${PRINTARGS} "${C_DEEPSKYBLUE4}${1} ${NO_FORMAT}"
}

# Pull and install MiniConda, if not installed
if ! command -v conda &> /dev/null
then
  echoInfo "Installing Miniconda"
  curl -L -o /tmp/miniforge.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh"
  chmod +x /tmp/miniforge.sh
  /tmp/miniforge.sh -b
  $HOME/mambaforge/bin/conda init --all
  $HOME/mambaforge/bin/conda config --set auto_activate_base false
  rm /tmp/miniforge.sh

  bash -l `basename "$0"`
  exit 0
fi

# Create a new conda environment for DarcyAI
echoInfo "Creating new environment for darcyai"
conda create --yes --name darcyai "python=3.8" "Pillow>=8.3.2" "numpy>=1.21.4"

# Activate our new env
echoInfo "Activating darcyai env"
conda activate darcyai

# Install all our deps
echoInfo "Installing all "
pip install --upgrade pip

# Install all our deps
pip install -q "opencv-python>=4.5.5.64"
pip install -q "imutils>=0.5.4"
pip install -q darcyai

# Install tensorflow for MA
$HOME/mambaforge/bin/conda install -y -c apple tensorflow-deps --force-reinstall
pip install -q tensorflow-macos
pip install -q tensorflow-metal

echoSuccess "Successfully installed all required libraries"

echoInfo "Testing tensorflow.."
python -c "import tensorflow as tf; print(tf.reduce_sum(tf.random.normal([1000, 1000])))"

echoSuccess "Successfully installed Tensorflow"

echo
echoInfo "The environment has been set up successfully."
echoInfo "Close your terminal, open a new one and run the following command:\n"
echoNotify "\t$ conda activate darcyai"
