# Setting up your Raspberry Pi for Darcy AI development

Raspberry Pi boards are excellent for building and running Darcy AI applications. This guide will show you how to get your RPi ready for Darcy AI development so you can run and debug your applications.

## Hardware you will need

- Raspberry Pi board (Pi 4 with 2GB+ of RAM recommended)
- Video camera attached to the camera port
- Google Coral edge TPU (USB version attached to USB 3.0 port)
- Micro SD card with at least 16GB capacity (32GB+ recommended)
- Power supply
    - 5 Volts with at least 3 Amps output for RPi4 (standard Raspberry Pi 4 power supply)
    - 5 Volts with at least 2.5 Amps output for RPi3 (most power supplies will qualify)

## Pick your Raspberry Pi operating system and flash your SD card

You can choose either a 32-bit or 64-bit Raspberry Pi OS. The instructions in this guide are the same for either operating system version, but note that using the newly released 64-bit version may result in some unforeseen issues because it is new and not all software packages in the ecosystem have been updated yet.

Follow the official Raspberry Pi Foundation instructions for getting your operating system and flashing it onto your Micro SD card. We recommend installing the Raspberry Pi OS with Desktop option because many helpful software packages will already be installed for you.

The Raspberry Pi SD card imager can be found here:
[https://www.raspberrypi.com/software/](https://www.raspberrypi.com/software/)

The Raspberry Pi OS versions can be downloaded here if you want to flash your SD card without the RPi Imager software:
[https://www.raspberrypi.com/software/operating-systems/](https://www.raspberrypi.com/software/operating-systems/)

## Enable SSH on your Raspberry Pi

Follow this guide to enable SSH on your Raspberry Pi board. Take these steps before you boot up the RPi for the first time by following the instructions in the first red box titled "NOTE" that begin with the words "For headless setup".

[https://www.raspberrypi.com/documentation/computers/remote-access.html#enabling-the-server](https://www.raspberrypi.com/documentation/computers/remote-access.html#enabling-the-server)

## Connect your Raspberry Pi to your network and the Internet

You can connect your RPi board using either a wired Ethernet connection or using WiFi. If you are using a wired connection, simply connect an Ethernet cable to your Raspberry Pi port and proceed to the next step.

If you are using WiFi, then you need to use one of the following approaches to add your WiFi network to your Raspberry Pi.

### Add your WiFi network via the Raspberry Pi desktop

If you are using the Raspberry Pi desktop and you have your RPi connected to a monitor, keyboard, and mouse then all you need to do is click on the WiFi icon in the upper-right toolbar area and add your WiFi network.

You will also want to open a terminal window so you can proceed with the next steps which use the command line.

### Add your WiFi network via the wpa_supplicant file

If you are not using the Raspberry Pi desktop then you will need to add your WiFi network using the file called `wpa_supplicant.conf`. This file is found under the `/etc/wpa_supplicant/` directory.

You can either add this file to the SD card before you boot up the Raspberry Pi or you can edit the file directly if you have a monitor, keyboard, and mouse attached to your RPi.

Follow the instructions provided by the Raspberry Pi Foundation to configure your `wpa_supplicant.conf` file.

[https://www.raspberrypi.com/documentation/computers/configuration.html#configuring-networking31](https://www.raspberrypi.com/documentation/computers/configuration.html#configuring-networking31)

## Find your Raspberry Pi board IP address

You will need to access your Raspberry Pi board using its hostname or IP address on your local network. This is true even if you are using a monitor, keyboard, and mouse with your RPi.

Follow the instructions provided by the Raspberry Pi Foundation to identify your RPi board on the network.

[https://www.raspberrypi.com/documentation/computers/remote-access.html#how-to-find-your-ip-address](https://www.raspberrypi.com/documentation/computers/remote-access.html#how-to-find-your-ip-address)

## Enable legacy camera support if you are using the newest Raspberry Pi OS

As of late 2021, the Raspberry Pi OS defaults to a camera configuration that is not compatible with many existing pieces of software. If you are using the newest Raspberry Pi OS, you must enable legacy camera support.

Open a command line terminal or SSH into your Raspberry Pi and type `sudo raspi-config`. Then go to ‘Interface Options’ and then ‘Legacy Camera’. Reboot when you are done.

## Python version

Python 3.9.x should already be installed in your Raspberry Pi. You can check the version by running the command `python --version`. You will need Python 3.5.x or greater to build with Darcy AI.

## Numpy package for Python

You will need the Numpy package for Python. Version 1.19.x should already be installed. You can check the version with the command `pip list | grep numpy` which will search for `numpy` in the entire list of installed Python packages.

If you do not have Numpy you can install it with the command `pip install numpy`. You should have Numpy 1.19.x or greater to build with Darcy AI.

## Pillow package for Python

You will need the Pillow package for Python. Version 8.1.x should already be installed. You can check the version with the command `pip list | grep Pillow`.

If you do not have Pillow installed, you can install it with `pip install Pillow`. You should have Pillow 8.1.x or greater to build with Darcy AI.

## imutils package for Python

Install the imutils package for Python with the command `pip install imutils`.

## DarcyAI package for Python

Install the DarcyAI pacakge for Python with the command `pip install darcyai`.

## Install Docker

You will need the Docker container runtime and command line tools installed on your Raspberry Pi. Install Docker with the following commands.

```
curl -fsSL https://get.docker.com -o get-docker.sh
```

This first command will download a convenient install script from Docker. Now run that script.

```
sudo sh get-docker.sh
```

Once Docker is installed, you need to add your standard user `pi` to the `docker` group so you can execute Docker commands without using `sudo`.

```
sudo usermod -aG docker pi
```

## Install Google Coral software libraries

You need the PyCoral and Edge TPU runtime software libraries installed on your Raspberry Pi. Follow the guide provided by Google and use the sections marked as "on Linux".

[https://coral.ai/docs/accelerator/get-started/#requirements](https://coral.ai/docs/accelerator/get-started/#requirements)

## Build OpenCV on your Raspberry Pi

This step is the most time consuming. Fortunately, if you use the convenient script provided by Q-Engineering, you should find it fairly easy to perform the build and installation of this very important piece of software. Start by making sure you have a large enough swap file. If you are using a Raspberry Pi 4 with 8GB of RAM then you might not need this step. A larger swap file allocation allows the RPi to use disk space in place of RAM. A lot of RAM is needed to build OpenCV. After you follow the swap file setup steps, you will find the convenient build script about one third down the page.

Expect to spend a couple of hours building OpenCV on your Raspberry Pi. Once this step is completed, you will have a modern version of OpenCV that is optimized for your Raspberry Pi board. This is worth doing, as you will use OpenCV in almost every computer vision application.

Version 4.5.5 of OpenCV is recommended. If you encounter a crash at the 99% build progress level, try changing the installation script to use `make -j2` instead of `make -j4`. It will take a little longer but should prevent the crash.

[https://qengineering.eu/install-opencv-4.5-on-raspberry-pi-4.html](https://qengineering.eu/install-opencv-4.5-on-raspberry-pi-4.html)

## Reboot your Raspberry Pi

You will need to reboot your Raspberry Pi after finishing all of these installation steps. Make sure your camera and your Google Coral USB device are attached to your RPi when you reboot.

```
sudo reboot
```

## Check for Google Coral USB device(s)

You can see which devices are attached to your Raspberry Pi using the command `lsusb`. This will display a list of devices. Look for an item that shows `Global Unichip Corp.`. You will have more than one of these items if you have more than one Google Coral USB device attached.

You will notice that once you start running a Darcy AI application, the value shown by `lsusb` will change to `Google, Inc.`. This is normal and expected and whenever you reboot your Raspberry Pi it will return to `Global Unichip Corp.` temporarily.

## Run the system check script

Run the script called `check.bash` to scan your Raspberry Pi and make sure everything is looking good. If you receive an error, use the error message to pinpoint which step needs to be completed or fixed.

## Start building your AI applications with Darcy

Go to the [Build Guide](/build/) and get started building with Darcy AI!
