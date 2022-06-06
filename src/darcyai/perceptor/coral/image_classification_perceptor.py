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

import cv2
import numpy as np
from typing import Any, List

from darcyai.config_registry import ConfigRegistry
from darcyai.perceptor.detected_class import Class
from darcyai.utils import validate_not_none, validate_type, validate, import_module

from .coral_perceptor_base import CoralPerceptorBase


class ImageClassificationPerceptor(CoralPerceptorBase):
    """
    ImageClassificationPerceptor is a class that implements the Perceptor interface for
    image classification.

    # Arguments
    threshold (float): The threshold for object detection.
    top_k (int): The number of top predictions to return.
    labels_file (str): The path to the labels file.
    labels (dict): A dictionary of labels.
    mean (float): The mean of the image.
    std (float): The standard deviation of the image.
    """


    def __init__(self,
                 threshold:float,
                 top_k:int=None,
                 labels_file:str=None,
                 labels:dict=None,
                 mean:float=128.0,
                 std:float=128.0,
                 **kwargs):
        super().__init__(**kwargs)

        dataset = import_module("pycoral.utils.dataset")
        self.__classify = import_module("pycoral.adapters.classify")
        self.__common = import_module("pycoral.adapters.common")

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
            self.__labels = dataset.read_label_file(labels_file)
        else:
            self.__labels = None

        validate_type(mean, (int, float), "mean must be a number")
        validate_type(std, (int, float), "std must be a number")

        self.interpreter = None
        self.__threshold = threshold
        self.__top_k = top_k
        self.__mean = mean
        self.__std = std
        self.__inference_shape = None


    # pylint: disable=unused-argument
    def run(self, input_data:Any, config:ConfigRegistry=None) -> List[Class]:
        """
        Runs the image classification model.

        # Arguments
        input_data (Any): The input data to run the model on.
        config (ConfigRegistry): The configuration for the perceptor.

        # Returns
        list[Class]: A list of detected classes.
        """
        resized_frame = cv2.resize(input_data, self.__inference_shape)

        params = self.__common.input_details(self.interpreter, "quantization_parameters")
        scales = params["scales"]
        zero_points = params["zero_points"]

        if abs(scales * self.__std - 1) < 1e-5 and abs(self.__mean - zero_points) < 1e-5:
            # Input data does not require preprocessing.
            self.__common.set_input(self.interpreter, resized_frame)
        else:
            normalized_frame = (np.asarray(resized_frame) - self.__mean) / (self.__std * scales) \
                + zero_points
            np.clip(normalized_frame, 0, 255, out=normalized_frame)
            self.__common.set_input(self.interpreter, normalized_frame.astype(np.uint8))

        self.interpreter.invoke()

        detected_classes = self.__classify.get_classes(
            self.interpreter,
            self.__top_k,
            self.__threshold)

        result = []
        for detected_class in detected_classes:
            if self.__labels is None:
                label = None
            else:
                label = self.__labels.get(detected_class.id, detected_class.id)
            result.append(Class(detected_class.id, label, detected_class.score))

        return result


    def load(self, accelerator_idx:[int, None]) -> None:
        """
        Loads the image classification model.

        # Arguments
        accelerator_idx (int): The index of the Edge TPU to use.
        """
        CoralPerceptorBase.load(self, accelerator_idx)

        input_shape = self.interpreter.get_input_details()[0]["shape"]
        self.__inference_shape = (input_shape[2], input_shape[1])
