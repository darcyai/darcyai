# Darcy AI Application Deployment Guide

Once you have built a Darcy AI application, you can deploy it to as many devices as you want. Use this guide to get devices set up on the [Darcy Cloud](https://cloud.darcy.ai) and create your own deployment YAML files and deploy your applications.

## Make sure your Darcy AI application container is available

If you followed the instructions in the [Build Guide](../build/) you probably created an application container called `darcydev/my-people-ai-app:1.0.0`. All Docker container identifiers are made of three parts. The first part, which is `darcydev` in this case, is the organization name. You must be a member of an organization in order to upload container images to that organization in [Docker Hub](https://hub.docker.com).

If you don't already have an account, create one now at [https://hub.docker.com](https://hub.docker.com). You will be given an organization which is your username.

If you used `darcydev` as your organization then you won't be able to upload your container image to Docker Hub. You can run your build command again but use a different container identifier and the build will be very quick. Docker will just make a copy of the container image with the new identifier.

The second part of the identifier is the container name. It comes after the `/` and it can be whatever you want. You can think of this as something like a file name. The third pard is the tag. It comes after the `:` and it can also be whatever you want. A standard practice is to use the tag to identify different versions of the same application container.

Once you have a new identifier for your Darcy AI application container and you have built the container image, you can add it to Docker Hub using the command `docker push YOUR_ORGANIZATION/YOUR_APP:tag.goes.here` where you have replaced the placeholders with the appropriate information, of course. You will use this identifier in your application deployment YAML file below.

## About the Darcy Cloud

The Darcy Cloud gives you management of all your edge devices and edge applications in one place. You can open an SSH shell session on demand, deploy applications, and see the health and status for every device. All of this functionality works no matter where your edge devices are physically located, even when they are behind NAT layers and firewalls. Use the Darcy Cloud to make building, deploying, and debugging easier, and then use it to operate your edge AI applications in production systems.

## Add your devices to the Darcy Cloud

If you don't already have an account, you can create one now for free. Create an account or log in at [https://cloud.darcy.ai](https://cloud.darcy.ai).

Once you are in your Darcy Cloud account, add your device as a node in your current project. Use the "plus button" in the bottom left to add a node. Follow the instructions in the pop-up window to add your device as a node.

<img src="https://github.com/darcyai/darcyai-sdk/raw/master/examples/screenshots/darcy-cloud-plus-item-button.png" height="100" />

## Create your application YAML

Here is a sample YAML file to work with.

```
kind: Application
apiVersion: iofog.org/v3
metadata:
  name: your-application-name
spec:
  microservices:
    - name: your-microservice-name
      agent:
        name: your-darcy-cloud-node-name
      images:
        arm: 'YOUR_ORGANIZATION/YOUR_APP:tag.goes.here'
        x86: 'YOUR_ORGANIZATION/YOUR_APP:tag.goes.here'
      container:
        rootHostAccess: true
        ports: []
        volumes:
          - containerDestination: /dev
            hostDestination: /dev
            type: bind
            accessMode: rw
```

You can find this sample YAMl file in the `examples/deploy/` directory called [app_deployment.yml](https://github.com/darcyai/darcyai-sdk/blob/master/examples/deploy/app_deployment.yml).

Your application deployment YAML file contains the information that the Darcy Cloud uses to load and run your Darcy AI application on any device. Replace the placeholder fields with your own information and save the file with whatever file name you like, such as `my-app-deploy.yml`.

For the agent name, which is shown above as `your-darcy-cloud-node-name` you should use the actual node name from your Darcy Cloud account. This is the name that shows for your device which you added in the steps above.

## Deploy your Darcy AI application

Now that you have all of the pieces, it's easy to deploy your application to your device or any other device. In the Darcy Cloud, click on the "plus button" in the bottom left and choose "app".

<img src="https://github.com/darcyai/darcyai-sdk/raw/master/examples/screenshots/darcy-cloud-plus-item-button.png" height="100" />

In the pop-up window, choose the "upload your app" option and you will see a drag-and-drop window on the right-hand side. You can drag and drop your YAML file into that window or you can click the "browse and upload" option and then select your YAML file.

<img src="https://github.com/darcyai/darcyai-sdk/raw/master/examples/screenshots/darcy-cloud-custom-app-deployment.png" />

The Darcy Cloud will tell you if you have any issues with your YAML file or your app deployment. It will also tell you if your Darcy AI application was deployed successfully. You can then check the status of your application using the Darcy Cloud.
