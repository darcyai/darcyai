# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

import time
from random import random

from darcyai.config import Config
from darcyai.perceptor.perceptor import Perceptor


class SamplePerceptor(Perceptor):
    def __init__(self, sleep=None, **kwargs):
        super().__init__(model_path="models/p1.tflite", **kwargs)

        if sleep is not None:
            self.__sleep = sleep
        else:
            self.__sleep = int(random() * 4) + 1

        self.set_config_schema([
            Config("bool_config", "bool config", "bool", False, "Boolean"),
            Config("int_config", "int config", "int", 2, "Integer"),
            Config("float_config", "float config", "float", 0.2, "Float"),
            Config("str_config", "str config", "str", "Something", "String"),
        ])


    def run(self, input_data, config):
        time.sleep(self.__sleep)

        return input_data

    
    def load(self, accelerator_idx=None):
        super().set_loaded(True)        
