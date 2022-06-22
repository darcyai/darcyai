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

# Add libraries we need
import time
from random import random

# Add Darcy AI libraries we need, particularly Perceptor base class and Config and Serializable
from darcyai.perceptor.perceptor import Perceptor
from darcyai.config import Config
from darcyai.serializable import Serializable


# Define a class called "BasicPOM" which is serializable which is a Perception Object Model (POM) compatible output
# The Darcy AI engine will add this POM-ready output to the POM which moves along the pipeline and to the output streams
class BasicPOM(Serializable):
    def __init__(self, value):
        super().__init__()

        self.__value = value

    def serialize(self):
        return {"value": self.__value}


# Define our custom Perceptor and call it "BasicPerceptor"
class BasicPerceptor(Perceptor):
    # Define our "init" method
    def __init__(self, sleep=0.05):
        # Call "init" on the parent class but don't pass an AI model path because we are just hard-coding our demo output
        super().__init__(model_path="")

        # Set up configuration items for this Perceptor
        self.set_config_schema([
            Config("int_config", "Integer Config",
                   "int", 666, "Integer Config"),
            Config("float_config", "Float Config",
                   "float", 6.66, "Float Config"),
            Config("str_config", "String Config",
                   "str", "Something", "String Config"),
            Config("bool_config", "Boolean Config",
                   "bool", True, "Boolean Config"),
        ])

        # Set up the list of named events that this Perceptor emits
        self.set_event_names([
            "event_1",
        ])

        # Set up some internal properties
        # If the sleep parameter is passed, use it
        # Otherwise set a random sleep
        self.__counter = 0
        if sleep is not None:
            self.__sleep = sleep
        else:
            self.__sleep = int(random() * 4) + 1

    # Define our "run" method
    def run(self, input_data, config):
        # Simply sleep for the configured amount of time
        time.sleep(self.__sleep)
        self.__counter += 1

        # Produce a simple text string output with the counter value so a consumer of this demo can see it is going up
        result = "Hello World #{}".format(self.__counter)

        # Emit the event called "event_1" so a consumer of this demo can subscribe to this type of event and see that it is working
        self.emit("event_1", result)

        # Wrap the output data in the BasicPOM type and send it out
        return BasicPOM(result)

    # Define our "load" method which does not need to do anything except set the value on the parent class
    def load(self, accelerator_idx=None):
        super().set_loaded(True)
