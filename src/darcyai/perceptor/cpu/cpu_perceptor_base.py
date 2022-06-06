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

import importlib.util

from darcyai.perceptor.perceptor import Perceptor
from darcyai.utils import import_module, validate_not_none, validate_type, validate

class CpuPerceptorBase(Perceptor):
    """
    Base class for all CPU Perceptors.
    """
    def __init__(self, num_cpu_threads:int=1, **kwargs):
        super().__init__(**kwargs)

        validate_not_none(num_cpu_threads, "num_cpu_threads is required")
        validate_type(num_cpu_threads, int, "num_cpu_threads must be an integer")
        validate(num_cpu_threads > 0, "num_cpu_threads must be greater than 0")

        if importlib.util.find_spec("tflite_runtime") is not None:
            tf = import_module("tflite_runtime.interpreter")
            self.__tf_interpreter = tf.Interpreter
        else:
            tf = import_module("tensorflow")
            self.__tf_interpreter = tf.lite.Interpreter

        self.__num_cpu_threads = num_cpu_threads

    def load(self) -> None:
        """
        Loads the perceptor.
        """
        self.interpreter = \
            self.__tf_interpreter(model_path=self.model_path, num_threads=self.__num_cpu_threads)
        self.interpreter.allocate_tensors()
        super().set_loaded(True)

    @staticmethod
    def read_label_file(filename:str, has_ids:bool=True, encoding:str="UTF-8") -> dict:
        """
        Reads the labels file.

        # Arguments
        filename (str): The path to the labels file.
        has_ids (bool): Whether the labels file contains IDs.
        encoding (str): The encoding of the labels file.

        # Returns
        dict: A dictionary containing the labels.
        """
        labels = {}

        with open(filename, "r", encoding=encoding) as file:
            for line in file:
                line = line.strip()
                if len(line) == 0:
                    continue
                if has_ids:
                    (class_id, label) = line.split(" ", maxsplit=1)
                    labels[int(class_id)] = label.strip()
                else:
                    labels[len(labels)] = line

        return labels
