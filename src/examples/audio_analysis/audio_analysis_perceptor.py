#Add libraries as needed, including TensorFlow Lite
import numpy as np
import os
import pathlib
import tflite_runtime.interpreter as tflite

#Add Darcy AI libraries needed, particularly Perceptor base class and Config
from darcyai.perceptor.perceptor import Perceptor
from darcyai.config import Config


#Define our custom Darcy AI Perceptor class
class AudioAnalysisPerceptor(Perceptor):
    """
    AudioAnalysisPerceptor is a Perceptor that can be used to analyze audio data.
    """
    def __init__(self):
        #Get the directory of our code and then get the TensorFlow Lite AI model file and the AI labels file
        script_dir = pathlib.Path(__file__).parent.absolute()
        model_file = os.path.join(script_dir, "sound_edgetpu.tflite")
        labels_file = os.path.join(script_dir, "labels.txt")

        #Call "init" on the parent class but pass our own AI model file
        super().__init__(model_path=model_file)

        #Default our AI interpreter to None (it will get used below)
        #Open the labels file and import the text values
        self.__interpreter = None
        with open(labels_file) as file:
            lines = file.readlines()
            self.__sound_names = [line.rstrip() for line in lines]

    #Define our "run" method which is where the Perceptor does its processing against the current data
    def run(self, input_data, config):
        """
        Run the audio analysis perceptor.

        # Arguments
        input_data (np.array): The input data to the perceptor.
            This is expected to be a [1, 193] float32 numpy array.
        config (Config): The configuration for the perceptor.
        """
        #Set the data into the AI model and retrieve the raw results
        self.__interpreter.set_tensor(self.__input_details[0]['index'], input_data)
        self.__interpreter.invoke()
        tflite_model_predictions = self.__interpreter.get_tensor(self.__output_details[0]['index'])

        #Break apart the raw results and the confidence levels
        #If the predictions meet a confidence threshold, list them as outputs
        ind = np.argpartition(tflite_model_predictions[0], -2)[-2:]
        ind[np.argsort(tflite_model_predictions[0][ind])]
        ind = ind[::-1]
        top_certainty = int(tflite_model_predictions[0, ind[0]] * 100)
        second_certainty = int(tflite_model_predictions[0, ind[1]] * 100)
        if top_certainty > 60:
            print(f"Top guess: {self.__sound_names[ind[0]]} ({top_certainty}%)")
            print(f"Second guess: {self.__sound_names[ind[1]]} ({second_certainty}%)")

    #Define our "load" method which is used by the Darcy AI Pipeline to set up our custom Percpetor
    def load(self, accelerator_idx=None):
        """
        Load the audio analysis perceptor.

        # Arguments
        accelerator_idx (int): The index of the Edge TPU accelerator to use.
        """
        #Set up our interpeter to use our own AI model and use the Coral Edge TPU library
        self.__interpreter = tflite.Interpreter(model_path=self.model_path, experimental_delegates=[tflite.load_delegate('libedgetpu.so.1')])
        self.__input_details = self.__interpreter.get_input_details()
        self.__output_details = self.__interpreter.get_output_details()

        self.__interpreter.allocate_tensors()

        super().set_loaded(True)
