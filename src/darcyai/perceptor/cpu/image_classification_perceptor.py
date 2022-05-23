# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

import collections
import cv2
import operator
import numpy as np
from typing import Any, List

from darcyai.config_registry import ConfigRegistry
from darcyai.perceptor.detected_class import Class
from darcyai.utils import validate_not_none, validate_type, validate

from .cpu_perceptor_base import CpuPerceptorBase


class ImageClassificationPerceptor(CpuPerceptorBase):
    """
    ImageClassificationPerceptor is a class that implements the Perceptor interface for
    image classification.

    # Arguments
    threshold (float): The threshold for object detection.
    top_k (int): The number of top predictions to return.
    labels_file (str): The path to the labels file.
    labels (dict): A dictionary of labels.
    quantized (bool): Whether the model is quantized.
    """


    def __init__(self,
                 threshold:float,
                 top_k:int=None,
                 labels_file:str=None,
                 labels:dict=None,
                 quantized:bool=True,
                 **kwargs):
        super().__init__(**kwargs)

        validate_not_none(threshold, "threshold is required")
        validate_type(threshold, (float, int), "threshold must be a number")
        validate(0 <= threshold <= 1, "threshold must be between 0 and 1")

        if top_k is not None:
            validate_type(top_k, int, "top_k must be an integer")
            validate(top_k > 0, "top_k must be greater than 0")

        if labels is not None:
            validate_type(labels, dict, "labels must be a dictionary")
            self.__labels = labels
        elif labels_file is not None:
            validate_type(labels_file, str, "labels_file must be a string")
            self.__labels = CpuPerceptorBase.read_label_file(labels_file)
        else:
            self.__labels = None

        validate_not_none(quantized, "quantized is required")
        validate_type(quantized, bool, "quantized must be a boolean")

        self.interpreter = None
        self.__threshold = threshold
        self.__top_k = top_k
        self.__quantized = quantized
        self.__input_details = None


    def run(self, input_data:Any, config:ConfigRegistry=None) -> List[Class]:
        """
        Runs the image classification model.

        # Arguments
        input_data (Any): The input data to run the model on.
        config (ConfigRegistry): The configuration for the perceptor.

        # Returns
        (list[Any], list(str)): A tuple containing the detected classes and the labels.
        """
        resized_input = cv2.resize(
            input_data, (self.__input_details[0]["shape"][1], self.__input_details[0]["shape"][2]))
        resized_input = resized_input.reshape(
            [1, self.__input_details[0]["shape"][1], self.__input_details[0]["shape"][2], 3])

        self.interpreter.set_tensor(self.__input_details[0]["index"], resized_input)
        self.interpreter.invoke()

        scores = self.interpreter.get_tensor(self.__output_details[0]["index"])[0]
        if self.__quantized:
            scale, zero_point = self.__output_details[0]["quantization"]
            scores = scale * (scores - zero_point)

        top_k = min(self.__top_k, len(scores)) if self.__top_k is not None else len(scores)
        clazz = collections.namedtuple("Class", ["id", "score"])
        classes = [
            clazz(i, scores[i])
            for i in np.argpartition(scores, -top_k)[-top_k:]
            if scores[i] >= self.__threshold
        ]
        detected_classes = sorted(classes, key=operator.itemgetter(1), reverse=True)

        result = []
        for detected_class in detected_classes:
            if self.__labels is None:
                label = None
            else:
                label = self.__labels[detected_class.id]
            result.append(Class(detected_class.id, label, detected_class.score))

        return result


    # pylint: disable=unused-argument
    def load(self, accelerator_idx:[int, None]) -> None:
        """
        Loads the image classification model.

        # Arguments
        accelerator_idx (int): Not used.
        """
        CpuPerceptorBase.load(self)
        self.__input_details = self.interpreter.get_input_details()
        self.__output_details = self.interpreter.get_output_details()
