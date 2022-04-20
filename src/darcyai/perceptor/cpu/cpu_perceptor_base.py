# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

from importlib import import_module
from typing import Union

from darcyai.perceptor.perceptor import Perceptor
from darcyai.utils import validate_type, validate

class CpuPerceptorBase(Perceptor):
    """
    Base class for all CPU Perceptors.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.__tf = import_module("tensorflow")

    def load(self) -> None:
        """
        Loads the perceptor.
        """
        self.interpreter = self.__tf.lite.Interpreter(model_path=self.model_path)
        self.interpreter.allocate_tensors()

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
