# Darcy AI Explorer Guide

The Darcy AI Explorer application is a great way to experience Darcy for the first time. This sample application is rich in features so you can get a sense for what Darcy provides you as a developer.

Follow the steps in this guide to get your device connected to the [Darcy Cloud](https://cloud.darcy.ai) and deploy the Darcy AI Explorer application.

## About the Darcy Cloud

The Darcy Cloud gives you management of all your edge devices and edge applications in one place. You can open an SSH shell session on demand, deploy applications, and see the health and status for every device. All of this functionality works no matter where your edge devices are physically located, even when they are behind NAT layers and firewalls. Use the Darcy Cloud to make building, deploying, and debugging easier, and then use it to operate your edge AI applications in production systems.

## Connect your device to the Darcy Cloud

If you don't already have an account, you can create one now for free. Create an account or log in at [https://cloud.darcy.ai](https://cloud.darcy.ai).

Once you are in your Darcy Cloud account, add your device as a node in your current project. Use the "plus button" in the bottom left to add a node to your project. Follow the instructions in the pop-up window to add your device as a node.

<img src="https://github.com/darcyai/darcyai-sdk/raw/master/examples/screenshots/darcy-cloud-plus-item-button.png" height="100" />

## Deploy the Darcy AI Explorer application

Click on the "plus button" and choose "app" to deploy a new application to your device. In the pop-up choose the "Darcy AI Explorer App" and then click "Next". Choose your device from the drop-down menu and then click "Deploy". The Darcy AI Explorer application will begin to download to your device. You can track the status of the app in the Darcy Cloud UI. When the app is listed as "Running" you can proceed to the next step. Depending on the Internet connection speed of your device, it may take about 15 minutes for the Darcy AI Explorer app to download and start on your device.

<img src="https://github.com/darcyai/darcyai-sdk/raw/master/examples/screenshots/darcy-cloud-explorer-app-deploy.png" />

## Open the Darcy AI Explorer

Once your Darcy AI Explorer app is running, you can view the UI and use the app by visiting the following URL in any browser. Replace `YOUR.DEVICE.IP.ADDRESS` with the actual IP address of your device. See Darcy AI in action and explore what it can do!
```
http://YOUR.DEVICE.IP.ADDRESS:5555/
```

## Continue your Darcy AI exploration

Now that you have a running Darcy AI application to explore, continue your journey by checking out the examples and getting started building your own application! [Darcy AI Documentation Home](https://github.com/darcyai/darcyai-sdk)