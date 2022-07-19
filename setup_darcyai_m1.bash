#!/usr/bin/env bash -l

#
# setup_darcyai_m1.bash - is a utlility script that will create a new Conda environment
# and install all of the required libraries needed by DarcyAI to be able to run successfully
# on one of the newer Apple M1 MacOS platforms.
#

set -e

# Pull and install MiniConda, if not installed
if ! command -v conda &> /dev/null
then
  echo "Installing Miniconda"
  wget "https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh" -O /tmp/miniforge.sh > /dev/null 2>&1
  chmod +x /tmp/miniforge.sh
  bash /tmp/miniforge.sh -b
  eval "$($HOME/mambaforge/bin/conda shell.bash hook)"
  rm /tmp/miniforge.sh
fi

# Create a new conda environment for DarcyAI
echo "Creating new environment for darcyai"
conda create --yes --name darcyai

# Activate our new env
echo "Activating darcyai env"
conda activate darcyai

# Install all our deps
echo "Installing all "
pip install --upgrade pip

# Install all our deps
pip install opencv-python>=4.5.5.64
pip install Pillow>=8.3.2
pip install numpy>=1.21.4
pip install imutils>=0.5.4
pip install -q darcyai

# Install tensorflow for MA
conda install -y -c apple tensorflow-deps --force-reinstall
pip install tensorflow-macos
pip install tensorflow-metal

echo "Successfully installed all required libraries"

echo "Testing tensorflow.."
python3 -c "import tensorflow as tf; print(tf.reduce_sum(tf.random.normal([1000, 1000])))"

echo "\nSuccessfully installed Tensorflow"

# If at some point you want to remove your Conda env, you can do so with `conda env remove -n darcyai`
