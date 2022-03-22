import time
from random import random

from darcyai.perceptor.perceptor import Perceptor
from darcyai.config import Config, RGB


class PerceptorMock(Perceptor):
    """
    Mock perceptor that generates random data.

    # Arguments
        mock (Mock): Mock object to be used for testing.
        sleep (float): Sleep time in seconds.
    """
    def __init__(self, sleep=None, mock=None, **kwargs):
        super().__init__(model_path="models/p1.tflite", **kwargs)

        self.config_schema = [
            Config("config_1", "str", "", "Config 1"),
            Config("config_2", "int", 0, "Config 2"),
            Config("config_3", "bool", False, "Config 3"),
            Config("config_4", "rgb", RGB(255, 255, 255), "Config 4"),
        ]

        self.event_names = ["event_1", "event_2"]

        if sleep is not None:
            self.__sleep = sleep
        else:
            self.__sleep = int(random() * 4) + 1

        self.__mock = mock

        self.__counter = 0

    def run(self, input_data, config):
        if self.__mock is not None:
            self.__mock.run(input_data)

        time.sleep(self.__sleep)

        self.__counter += 1
        return f"Hello!!! {self.__counter}"

    def load(self, accelerator_idx=None):
        if self.__mock is not None:
            self.__mock.load(accelerator_idx=None)

        super().set_loaded(True)

    def get_event_names(self):
        return ["event_1", "event_2"]
