# Setting up your Windows environment for Darcy AI development

You can use any Windows computer to build Darcy AI applications. After you finish setting up your computer as a development environment, you will be able to write, test, and debug your Darcy AI apps. Then you can package your code and deploy the applications to any edge device!

## What you will need

- Windows laptop or desktop
- A video camera that you want to use (a built-in webcam or USB webcam works very well for this purpose)
- 5GB or more of free disk space to accommodate code libraries and application container images
- Any IDE software that will allow you to write and debug Python (use your favorite IDE)

## Install Python 3.6.9 or greater

If you do not already have Python version 3.6.9 or greater, you will need to install it now. Darcy AI requires this version of Python or higher. Note that Python 2.x versions are also not compatible with Darcy AI. You need Python 3 and the `darcyai` library will not install with versions below 3.6.9.

Download and install the latest or your preferred version of Python3 from Python.org directly [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/).

If you have both Python 2.x versions and Python 3.x versions on your Windows machine, you may need to use `python3` and `pip3` for all of the commands instead of just `python` and `pip`. You can make adjustments to how Python gets launched on your Windows computer if you want by following this guide [https://docs.python.org/3/using/windows.html#python-launcher-for-windows](https://docs.python.org/3/using/windows.html#python-launcher-for-windows).

## Install OpenCV

Install the OpenCV package for Python with the command `py -m pip install opencv-python`

## Install the Pillow library

Install the Pillow package for Python with the command `py -m pip install Pillow`.

### Install the Numpy library

Install the numpy package for Python with the command `py -m pip install numpy`.

### Install the Imutils library

Install the imutils package for Python with the command `py -m pip install imutils`.

## Install the DarcyAI library

Install the Darcy AI library for Python with the command `py -m pip install darcyai`.

## Install Docker for Windows

If you don't already have Docker on your Mac, install it now by following the official instructions [https://docs.docker.com/desktop/windows/install/](https://docs.docker.com/desktop/windows/install/).

After you have installed Docker, you can use `docker` commands on the command line. You will be using these commands to package your Darcy AI applications for deployment, including deploying to edge devices that are a different CPU architecture than your Windows machine! To make sure you can use the latest Docker build commands like `buildx` you can enable experimental features using this guide [https://docs.docker.com/desktop/windows/#command-line](https://docs.docker.com/desktop/windows/#command-line). This will tell Docker to allow use of the latest tools which will save you a lot of time when packaging your apps!

## Install TensorFlow

Install TensorFlow for Python with the command `py -m pip install tensorflow`

## Start building your AI applications with Darcy

Go to the [Build Guide](../build/) and get started building with Darcy AI!
