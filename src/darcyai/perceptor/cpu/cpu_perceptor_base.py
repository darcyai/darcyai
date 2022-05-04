# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

import importlib

from darcyai.perceptor.perceptor import Perceptor
from darcyai.utils import import_module

class CpuPerceptorBase(Perceptor):
    """
    Base class for all CPU Perceptors.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if importlib.util.find_spec("tensorflow") is None:
            tf = import_module("tflite_runtime.interpreter")
            self.__tf_interpreter = tf.Interpreter
        else:
            tf = import_module("tensorflow")
            self.__tf_interpreter = tf.lite.Interpreter

    def load(self) -> None:
        """
        Loads the perceptor.
        """
        self.interpreter = self.__tf_interpreter(model_path=self.model_path)
        self.interpreter.allocate_tensors()
        super().set_loaded(True)        

    @staticmethod
    def read_label_file(filename:str, has_ids:bool=True) -> dict:
        """
        Reads the labels file.

        Arguments:
            filename (str): The path to the labels file.
            has_ids (bool): Whether the labels file contains IDs.

        Returns:
            dict: A dictionary containing the labels.
        """
        labels = {}

        with open(filename, "r") as file:
            for line in file:
                line = line.strip()
                if len(line) == 0:
                    continue
                if has_ids:
                    (id, label) = line.split(" ", maxsplit=1)
                    labels[int(id)] = label.strip()
                else:
                    labels[len(labels)] = line

        return labels