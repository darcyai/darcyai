# Audio Analysis Sample Application

This sample application is a good example of a custom input stream and a custom perceptor working together to extend Darcy AI to process audio in real time.

## Requirements

You will need a microphone connected to the computer that is running this Darcy AI application. The built-in microphone for most computers should work.

## Run the example

Use this command to run the main Python file which is the application code:

```
python3 -u audio_analysis.py
```

The other files are the TensorFlow AI model, custom Perceptor, and custom Input Stream that make the application possible.

## Expected results

The application will run successfully and continue to run. The terminal output will show how Darcy AI detects and labels each sound as it occurs.

For more information about building with Darcy AI, see the [Build Guide](https://docs.darcy.ai/docs/guides/build/).