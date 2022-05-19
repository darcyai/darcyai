# Setting up your Jetson Nano for Darcy AI development

Nvidia Jetson Nano boards are excellent for building and running Darcy AI applications. This guide will show you how to get your Nano ready for Darcy AI development so you can run and debug your applications.

Note that you will be using a Google Coral AI accelerator attached to your Jetson Nano. Although the Jetson Nano board contains an Nvidia GPU, the Darcy AI platform currently requires a Google Coral accelerator in order to operate. New editions of Darcy AI that take advantage of the Nvidia GPU will be available soon.

## Hardware you will need

- Nvidia Jetson Nano board (Nano developer kit version with 4GB of RAM recommended)
- Video camera attached to the camera port (any camera compatible with Raspberry Pi or any USB camera will work)
- Google Coral edge TPU (USB version attached to USB 3.0 port)
- Micro SD card with 32GB+ capacity and UHS-1 speed rating or faster
- Power supply with 5.5mm barrel plug at 5 Volts DC with at least 3 Amps output
- Jumper for power pins on Nano board (alternative hardware suggested below)

## Follow the Nvidia Jetston Nano guide to setup your board

You will need to flash your SD card with the operating system and developer tools provided by Nvidia. Then your Jetson Nano will boot to the operating system and allow you to SSH into the board. Nvidia provides an excellent guide for getting started. It includes instructions for users on Windows, Mac OS, and Linux computers.

If you are using the "headless" setup approach, you will need to put a jumper on your Nano board on pin header J48. You can use a standard 2-pin motherboard jumper but you can also use any approach that will make an electrical connection between these two pins. One approach is to use one end of an aligator clip by attaching the jaws across both pins.

Follow the official Jetson Nano guide here:
[https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit](https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit)

## Open a command line session

The goal of the prior step is to get your Jetson Nano set up with JetPack and an operating system so it will boot. If you accomplished the prior step successfully, you should be able to use SSH, terminal session over USB, or an attached keyboard, monitor, and mouse to open a command line session. No matter which approach you used to setup your Jetson Nano (headless or attached monitor), you should now be able to log in and see a command line prompt.

## Linux package manager update

Next you will be installing a set of software packages. Some of them are Python packages and some are Linux packages. Start by updating the Ubuntu package manager with the following command. It may take a minute or two.

```
sudo apt-get update
```

### Install curl

Curl is a very useful package for downloading files from the command line. You will use it later when installing the Google Coral software. Install it now with the following command.

```
sudo apt-get install curl
```

### Install JPEG codec

In order for some Python packages to work, your Jetson Nano needs to have a JPEG image codec available. A JPEG library is not installed by default with the JetPack software. Install one with this command.

```
sudo apt-get install libjpeg-dev
```

## Install Pip3 package manager for Python3

By default, the JetPack software installs Python 3.6.9 and also a version of Python 2.7. The package manager for Python, called Pip, is only installed for the Python 2.7 version. You need to install Pip3 which is a Python3 package manager. Use the following command to install Pip3.

```
sudo apt-get install python3-pip
```

## Edit .bashrc file to use Python3 and Pip3

Now that Pip3 has been installed, you need to edit a file that will make Python3 your default so you can just use the word `python` in your commands instead of `python3`. You will also be able to just use `pip` for installing Pip3 packages after you make this edit.

You can use the `vi` editor as in the example here or you can use any other text editor you prefer. Use this command to begin editing your `.bashrc` file.

```
vi ~/.bashrc
```

Navigate to the bottom of the file. You will add two lines to the very end of the file. Add the following lines.

```
alias python=python3
alias pip=pip3
```

Save the file and exit the editor. If you are using the `vi` editor you can do this by pressing the `esc` key and then typing `:wq` and pressing `enter`.

Now that you have edited the file, it will take effect every time you log in. And now when you use `python` in a command, it will use Python3 and every time you use `pip` in a command it will use Pip3.

Activate the edited `.bashrc` file now so you don't have to wait until the next login. Use the following command.

```
source ~/.bashrc
```

## Install Pillow Python library

Install the imutils package for Python with the command `pip install Pillow`.

## Install imutils Python library

Install the imutils package for Python with the command `pip install imutils`.

## Install DarcyAI Python library

Install the DarcyAI pacakge for Python with the command `pip install darcyai`.

## Add your user to the Docker Linux group

Docker is installed by default on your Jetson Nano when you use the JetPack software package from Nvidia. You need to add your Ubuntu Linux user to the `docker` group so you can execute Docker commands without using `sudo`. Your username is the login name you chose during the Jetson Nano setup process at the start of this guide. Replace the word YOURUSER shown below with your actual user such as `darcydev`

```
sudo usermod -aG docker YOURUSER
```

## Install Google Coral software libraries

You need the PyCoral and Edge TPU runtime software libraries installed on your Jetson Nano. Follow the guide provided by Google and use the sections marked as "on Linux".

[https://coral.ai/docs/accelerator/get-started/#requirements](https://coral.ai/docs/accelerator/get-started/#requirements)

## Reboot your Jetson Nano

You will need to reboot your Jetson Nano after finishing all of these installation steps. Make sure your camera and your Google Coral USB device are attached to your Nano board when you reboot.

```
sudo reboot
```

## Check for Google Coral USB device(s)

You can see which devices are attached to your Jetson Nano using the command `lsusb`. This will display a list of devices. Look for an item that shows `Global Unichip Corp.`. You will have more than one of these items if you have more than one Google Coral USB device attached.

You will notice that once you start running a Darcy AI application, the value shown by `lsusb` will change to `Google, Inc.`. This is normal and expected and whenever you reboot your Nano board it will return to `Global Unichip Corp.` temporarily.

## Run the system check script

Run the script called `check.bash` to scan your Jetson Nano and make sure everything is looking good. If you receive an error, use the error message to pinpoint which step needs to be completed or fixed. If you receive a message that everything is looking good, then you are ready to build with Darcy AI!

## Start building your AI applications with Darcy

Go to the [Build Guide](../build/) and get started building with Darcy AI!
