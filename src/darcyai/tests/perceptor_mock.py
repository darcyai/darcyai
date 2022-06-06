# Copyright 2022 Edgeworx, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

        self.set_config_schema([
            Config("config_1", "Config 1", "str", "", "Config 1 Description"),
            Config("config_2", "Config 2", "int", 0, "Config 2 Description"),
            Config("config_3", "Config 3", "bool", False, "Config 3 Description"),
            Config("config_4", "Config 4", "rgb", RGB(255, 255, 255), "Config 4 Description"),
        ])

        self.set_event_names(["event_1", "event_2"])

        if sleep is not None:
            self.__sleep = sleep
        else:
            self.__sleep = int(random() * 4) + 1

        self.__mock = mock

        self.__counter = 0

    # pylint: disable=unused-argument
    def run(self, input_data, config):
        if self.__mock is not None:
            self.__mock.run(input_data)

        time.sleep(self.__sleep)

        self.__counter += 1
        return f"Hello!!! {self.__counter}"

    # pylint: disable=unused-argument
    def load(self, accelerator_idx=None):
        if self.__mock is not None:
            self.__mock.load(accelerator_idx=None)

        super().set_loaded(True)

    def get_event_names(self):
        return ["event_1", "event_2"]
