# Darcy AI SDK

This is the official software development kit (SDK) for building on the Darcy AI platform.

To browse this document and all of the other documentation on a local web server, run the [apidocs.bash](https://github.com/darcyai/darcyai/blob/main/apidocs.bash) script and then visit [http://localhost:8000](http://localhost:8000).

## Introducing the Darcy AI platform

Darcy is an artificial intelligence (AI) that is focused on real-time interactions with the world. It has a variety of senses, such as vision and hearing, that allow it to perceive the local environment. You can give Darcy additional senses, such as LiDAR or thermal vision, to expand its capabilities. Darcy is present in every device where a Darcy AI application is running. It runs entirely in each device. No data needs to leave the device and no computation is done in the cloud.

Darcy was designed to bring AI technology into the real world while keeping privacy and security as top priorities. Building real-time AI applications is very challenging. The Darcy AI SDK is a developer platform for computer vision and other applications which handles all of the most difficult and repetitive problems for you so you can focus on building amazing solutions.

With the Darcy AI SDK, you get everything you need to build real-time AI applications. If you can write web applications with Node.js or you have moderate Python experience, then you can develop a fully functioning AI app with Darcy. The SDK comes with documentation, build instructions, example applications, and more.

## How to use this SDK

Use this document and the other markdown files in this directory to learn about the Darcy AI platform and to get started. The guide documents will take you from an absolute beginner to building and deploying your own Darcy AI applications. The [docs](https://github.com/darcyai/darcyai/blob/main/docs) folder contains the full technical Darcy AI programming documentation.

To browse this document and all of the other documentation on a local web server, run the [apidocs.bash](https://github.com/darcyai/darcyai/blob/main/apidocs.bash) script and then visit [http://localhost:8000](http://localhost:8000).

## What you need

To develop and package Darcy AI applications, you only need a Mac, Windows, or Linux computer. To run Darcy AI applications on devices, you just need one or more devices that meet the minimum requirements below.

### System requirements for developer environments

- Any modern CPU (both x86 and ARM processors will work)
- 4GB of RAM
- Camera (the integrated webcam on most laptops will work)
- 5GB of available disk space for Docker, Python, required libraries, and your application containers
- Optional: Google Coral AI accelerator for testing accelerated processing

### System requirements for running deployed Darcy AI applications

- ARM or x86 CPU (two or more cores recommended)
- Google Coral AI accelerator (more than one Coral increases performance for many applications)
- 512MB of RAM (4GB or more recommended)
- Camera (required for using Darcy with live video)
- Internet connectivity (wired Ethernet or WiFi)
- 200MB available disk space (1GB or more recommended and your application size will vary)

### Darcy AI ready edge boards

- Raspberry Pi with Coral USB
	- Raspberry Pi 4 single board computer [https://www.raspberrypi.com/products/raspberry-pi-4-model-b/](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)
	- Google Coral AI accelerator USB module [https://coral.ai/products/accelerator/](https://coral.ai/products/accelerator/)
- Nvidia Jetson Nano with Coral USB
	- Jetson Nano Developer Kit [https://developer.nvidia.com/embedded/jetson-nano-developer-kit](https://developer.nvidia.com/embedded/jetson-nano-developer-kit)
	- Google Coral AI accelerator USB module [https://coral.ai/products/accelerator/](https://coral.ai/products/accelerator/)
- Google Coral Dev Board [https://coral.ai/products/dev-board/](https://coral.ai/products/dev-board/)
- Google Coral Dev Board Mini [https://coral.ai/products/dev-board-mini/](https://coral.ai/products/dev-board-mini/)
- ASUS Tinker T [https://www.asus.com/us/Networking-IoT-Servers/AIoT-Industrial-Solutions/Tinker-Board-Series/Tinker-Edge-T/](https://www.asus.com/us/Networking-IoT-Servers/AIoT-Industrial-Solutions/Tinker-Board-Series/Tinker-Edge-T/)

## Getting started

If you haven't already become familiar with the Darcy AI platform terminology, check out this [Terminology Guide](../terminology/) to get up to speed quickly.

The best way to get started with Darcy is to see it in action. Start by trying out the Darcy AI Explorer application in the [Darcy Explorer Guide](../darcy-ai-explorer/).

When you are ready to create, you can launch your Darcy AI developer journey with the [Getting Started Guide](../getting-started/).

## Building

To prepare your Mac OS computer as a development environment for building Darcy AI applications, follow the [Mac OS X Environment Setup Guide](../macos-setup/).

To prepare your Windows computer as a development environment for building Darcy AI applications, follow the [Windows Environment Setup Guide](../windows-setup/).

Learn how to build and run a Darcy AI application using your favorite IDE with the [Build Guide](../build/).

## Packaging

Learn how to package your Darcy AI application into a container that includes all of the dependencies needed to run on many different devices with the [Packaging Guide](../package/).

## Deploying

Learn how to deploy your Darcy AI application to your edge devices using the Darcy Cloud in the [Deployment Guide](../deploy/).

## Documentation

Open the Darcy AI technical documentation to search and browse the API with code examples. This is a local documentation site that will run directly in your browser. The documentation is specific to each version of the Darcy AI SDK so it's the best place to reference when building. To browse this document and all of the other documentation on a local web server, run the [apidocs.bash](https://github.com/darcyai/darcyai/blob/main/apidocs.bash) script and then visit [http://localhost:8000](http://localhost:8000).

If you prefer to access the latest Darcy AI developer documentation with an internet connection, use [Hosted Darcy AI Documentation](https://darcyai.github.io/darcyai-sdk/).

## Resources

### Examples

The [examples](https://github.com/darcyai/darcyai/blob/main/src/examples) folder contains a diverse set of sample applications that you can use as a reference or as a start of your own Darcy AI application. The code is commented to help you understand what to do and when to do it. Here are some short descriptions to help you understand what examples are available. Some example applications are stored in their own code repositories to make learning and building easier.

- Darcy AI Explorer - this demo application is a rich showcase of what the Darcy AI system can do. Use the source code as a model for building a full-featured production application. [https://github.com/darcyai/darcyai-explorer](https://github.com/darcyai/darcyai-explorer)

- Real-time Audio Analysis - Build and deploy this Darcy AI demo application to learn how to add audio capabilities to Darcy and listen for important sounds. [Audio Analysis](https://github.com/darcyai/darcyai/blob/main/src/examples/audio_analysis)

- Basic Darcy AI [Pipeline](../terminology/#pipeline) - Use this demo application to learn the basics of creating a Darcy AI Pipeline. [Basic Pipeline](https://github.com/darcyai/darcyai/blob/main/src/examples/basic_pipeline)

- Sample [Output Stream](../terminology/#output-stream) - Learn how to create a Darcy AI Output Stream by adding this example to your application. The example sends your Darcy AI output to an Amazon Web Services S3 bucket. [Output Stream](https://github.com/darcyai/darcyai/blob/main/src/examples/output_streams)

- Sample [Perceptors](../terminology/#perceptor) - Learn how to build your own Darcy AI Perceptors with the examples in this directory. There is a basic mock perceptor that you can use as a template. There is a face detector perceptor that uses an [AI model](../terminology/#ai-model) to find faces. There is also a face mask detector perceptor that checks a person's face for a mask. [Perceptors](https://github.com/darcyai/darcyai/blob/main/src/examples/perceptors)

- Heart Rate Demo - this demo application is a good example of how to build an edge application that is made of multiple microservices that communicate with each other. [https://github.com/darcyai/heart-rate-demo](https://github.com/darcyai/heart-rate-demo)

- Sample Build Files - Get a sample Dockerfile in this folder so you don't have to create one from scratch. [Build Files](https://github.com/darcyai/darcyai/blob/main/src/examples/build)

- Sample Deployment Files - Get a sample application YAML file in this folder so you can just replace the default values and deploy your edge AI application easily. [Deployment Files](https://github.com/darcyai/darcyai/blob/main/src/examples/deploy)

### Getting help

- Get help from the other Darcy AI developers, the Darcy team, and the whole Darcy community on the Darcy AI Forum at [https://discuss.darcy.ai/c/darcy-ai/](https://discuss.darcy.ai/c/darcy-ai/)
- Report and track bugs in the Darcy AI platform and SDK using Github issues [https://github.com/darcyai/darcyai/issues](https://github.com/darcyai/darcyai/issues)

### Python packages for Darcy AI
- Darcy AI package [https://pypi.org/project/darcyai/](https://pypi.org/project/darcyai/)

### Darcy Cloud
Deploy and manage edge applications including Darcy AI applications with the Darcy Cloud. Create an account for free at [https://cloud.darcy.ai](https://cloud.darcy.ai)

### Other helpful links
- Company website for Edgeworx, the providers of the Darcy AI platform [https://darcy.ai](https://darcy.ai)
- Official website for the Tensorflow AI project [https://www.tensorflow.org](https://www.tensorflow.org)