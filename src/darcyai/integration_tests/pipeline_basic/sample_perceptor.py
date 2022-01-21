import time
from random import random

from darcyai.perceptor.perceptor import Perceptor


class SamplePerceptor(Perceptor):
    def __init__(self, sleep=None, **kwargs):
        super().__init__(model_path="models/p1.tflite", **kwargs)

        if sleep is not None:
            self.__sleep = sleep
        else:
            self.__sleep = int(random() * 4) + 1


    def run(self, input_data, config):
        time.sleep(self.__sleep)

        return input_data

    
    def load(self, accelerator_idx=None):
        super().set_loaded(True)        
