# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

import cv2
from typing import Any, List

from darcyai.config_registry import ConfigRegistry
from darcyai.perceptor.detected_object import Object
from darcyai.utils import validate_not_none, validate_type, validate, import_module

from .coral_perceptor_base import CoralPerceptorBase


class ObjectDetectionPerceptor(CoralPerceptorBase):
    """
    ObjectDetectionPerceptor is a class that implements the Perceptor interface for
    object detection.

    # Arguments
    threshold (float): The threshold for object detection.
    labels_file (str): The path to the labels file.
    labels (dict): A dictionary of labels.
    """


    def __init__(self, threshold:float, labels_file:str=None, labels:dict=None, **kwargs):
        super().__init__(**kwargs)

        dataset = import_module("pycoral.utils.dataset")
        self.__detect = import_module("pycoral.adapters.detect")
        self.__common = import_module("pycoral.adapters.common")

        validate_not_none(threshold, "threshold is required")
        validate_type(threshold, (float, int), "threshold must be a number")
        validate(0 <= threshold <= 1, "threshold must be between 0 and 1")

        if labels is not None:
            validate_type(labels, dict, "labels must be a dictionary")
            self.__labels = labels
        elif labels_file is not None:
            validate_type(labels_file, str, "labels_file must be a string")
            self.__labels = dataset.read_label_file(labels_file)
        else:
            self.__labels = None

        self.interpreter = None
        self.__threshold = threshold

    # pylint: disable=unused-argument
    def run(self, input_data:Any, config:ConfigRegistry=None) -> List[Object]:
        """
        Runs the object detection model on the input data.

        # Arguments
        input_data (Any): The input data to run the model on.
        config (ConfigRegistry): The configuration for the Perceptor.

        # Returns
        list[Object]: A list of detected objects.
        """
        _, scale = self.__common.set_resized_input(
            self.interpreter,
            (input_data.shape[1], input_data.shape[0]),
            lambda size: cv2.resize(input_data, size))

        self.interpreter.invoke()

        detected_objects = self.__detect.get_objects(self.interpreter, self.__threshold, scale)

        result = []
        for detected_object in detected_objects:
            if self.__labels is None:
                label = None
            else:
                label = self.__labels.get(detected_object.id, detected_object.id)
            result.append(Object(
                detected_object.id,
                label,
                detected_object.score,
                max(detected_object.bbox.xmin, 0),
                max(detected_object.bbox.ymin, 0),
                detected_object.bbox.xmax,
                detected_object.bbox.ymax))

        return result


    def load(self, accelerator_idx:[int, None]) -> None:
        """
        Loads the object detection model.

        # Arguments
        accelerator_idx (int): The index of the Edge TPU to use.

        # Returns
        None
        """
        CoralPerceptorBase.load(self, accelerator_idx)
