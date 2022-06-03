# Darcy AI platform terminology guide

Before you begin building with Darcy AI or testing its functionality, you need to understand the terminology and basic architecture. This document will give you an understanding quickly.

## Engine

The Darcy AI engine is the part that runs the AI computations and manages the system resources such as memory and CPU threads. It can be considered the core “backend code” of Darcy AI. As a developer, you do not need to interact with the engine directly. You only need to use the provided interfaces in the API as described in the documentation.

## Pipeline

Every Darcy AI application is allowed one pipeline. A Darcy AI pipeline is the sequenced set of AI processes that does the real work in the application. The Darcy AI pipeline code object is one of the main objects that you will interact with as a developer. It contains many important methods and the AI processing starts when the “run()” method is called.

## Perceptor

A Darcy AI perceptor is a code module that integrates raw AI processing with CPU code to make an easy-to-use semantic interface for the underlying AI output. Perceptors are built by developers who understand AI programming but are used by AI application developers who want to leverage the perceptor abilities. This frees AI application developers from needing to become AI experts and opens a perceptor library ecosystem.

## Perception Object Model (POM)

Similar to the Document Object Model (DOM) that is found in web browsers, the Perception Object Model (POM) is a data tree structure found in Darcy AI applications. The POM is the place where the outputs of each pipeline step are stored. The POM is available to Darcy AI application developers at each pipeline step, when a whole pipeline cycle has been completed, and at any point when the developer desires to interact with it. The POM also contains a history of all AI raw inputs and processing results.

## Input Stream

A Darcy AI input stream is the source data that is used for AI processing. Because Darcy’s “senses” can be expanded to include any source of data, an input stream code object is used to encapsulate the processing that is done to prepare incoming data for AI workloads. An example of an input stream code library is one that captures the frames of video from a camera and also merges the thermal camera data with each frame, even though the two cameras provide data at different rates. An input stream is attached to a pipeline by you, the Darcy AI application developer.

## Output Stream

A Darcy AI output stream is a code library that receives the data from the pipeline processing and produces a useful output, such as a video display or a CSV file. Many output streams can be attached to a single pipeline by you, the Darcy AI application developer.

## Callback

For every step in the Darcy AI application processing, work is needed to format and produce business value from incoming data and outgoing data. The way that Darcy allows developers to do this work is to have their code processed by Darcy when the time is right. This is called a “callback” and it is a well-known pattern of software development in JavaScript and other languages. By using callbacks, developers can focus on just the pieces of code that relate to their actual application and know that Darcy will run their code for them.

## Frame, Cycle, or Pulse

Every complete trip through a Darcy AI pipeline is called a frame. It can also be called a cycle or a pulse.

## Initialization

In order to allow Darcy to start doing AI processing, some foundational settings must be chosen and some basic requirements must be met, such as providing an input stream. Then the Darcy AI pipeline needs to be started so the application can run. These steps are called the Darcy AI initialization and they must be performed by the developer in every application.

## Docker Base Image

There are many software packages and libraries that Darcy AI applications need in order to build and run properly. Asking you, the developer, to know and understand these dependencies would slow you down and cause you unecessary complexity. To circumvent this problem, the required software is bundled ahead of time in easy-to-use base images that are Docker containers. Because they are already Docker containers, you can make your application Docker containers easily by starting from one of the provided base container images.

## Performance Metrics

Darcy tracks system performance when doing AI processing. Each trip through the pipeline steps is measured, along with the individual pipeline steps. Darcy AI application developers can request this performance data in their application, which allows for benchmarking, profiling, and innovative displays that show how fast each part of Darcy’s work is being done.

## AI Model

The actual AI neural network processing is done using AI models. An AI model is a stored image of a neural net that was built during an AI training or retraining process. Most developers use AI models that already exist and were created by someone else. Darcy AI perceptors contain AI models and make them easier to use. Most Darcy AI application developers do not need to use AI models directly because of the perceptor architecture.