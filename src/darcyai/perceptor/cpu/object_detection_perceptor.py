# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

import cv2
from typing import Any, List

from darcyai.config_registry import ConfigRegistry
from darcyai.perceptor.detected_object import Object
from darcyai.utils import validate_not_none, validate_type, validate

from .cpu_perceptor_base import CpuPerceptorBase


class ObjectDetectionPerceptor(CpuPerceptorBase):
    """
    ObjectDetectionPerceptor is a class that implements the Perceptor interface for
    object detection.

    # Arguments
    threshold (float): The threshold for object detection.
    labels_file (str): The path to the labels file.
    labels (dict): A dictionary of labels.
    quantized (bool): Whether the model is quantized.
    """


    def __init__(self,
                 threshold:float,
                 labels_file:str=None,
                 labels:dict=None,
                 quantized:bool=True,
                 **kwargs):
        super().__init__(**kwargs)

        validate_not_none(threshold, "threshold is required")
        validate_type(threshold, (float, int), "threshold must be a number")
        validate(0 <= threshold <= 1, "threshold must be between 0 and 1")

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
        self.__quantized = quantized
        self.__input_details = None
        self.__output_details = None

    def run(self, input_data:Any, config:ConfigRegistry=None) -> List[Object]:
        """
        Runs the object detection model on the input data.

        # Arguments
        input_data (Any): The input data to run the model on.
        config (ConfigRegistry): The configuration for the Perceptor.

        # Returns
        (list[Any], list(str)): A tuple containing the detected objects and the labels.
        """

        resized_input = cv2.resize(
            input_data, (self.__input_details[0]["shape"][1], self.__input_details[0]["shape"][2]))
        resized_input = resized_input.reshape(
            [1, self.__input_details[0]["shape"][1], self.__input_details[0]["shape"][2], 3])

        self.interpreter.set_tensor(self.__input_details[0]["index"], resized_input)
        self.interpreter.invoke()

        det_boxes = self.interpreter.get_tensor(self.__output_details[0]["index"])[0]
        det_classes = self.interpreter.get_tensor(self.__output_details[1]["index"])[0]
        det_scores = self.interpreter.get_tensor(self.__output_details[2]["index"])[0]
        if self.__quantized:
            scale, zero_point = self.__output_details[0]["quantization"]
            det_scores = scale * (det_scores - zero_point)

        result = []
        for idx, score in enumerate(det_scores):
            if score < self.__threshold:
                break
            if self.__labels is None:
                label = None
            else:
                label = self.__labels[int(det_classes[idx])]
            bbox = self.__scale(input_data.shape, det_boxes[idx])
            result.append(Object(
                int(det_classes[idx]),
                label,
                score,
                int(max(bbox[0], 0)),
                int(max(bbox[1], 0)),
                int(bbox[2]),
                int(bbox[3])))

        return result


    # pylint: disable=unused-argument
    def load(self, accelerator_idx:[int, None]=None) -> None:
        """
        Loads the object detection model.

        # Arguments
        accelerator_idx (int): Not used.
        """
        CpuPerceptorBase.load(self)
        self.__input_details = self.interpreter.get_input_details()
        self.__output_details = self.interpreter.get_output_details()

    def __scale(self, input_shape, bbox):
        """
        Scales the bounding box.

        # Arguments
        input_shape (tuple): The shape of the input data.
        bbox (tuple): The bounding box to scale.

        # Returns
        tuple: The scaled bounding box.
        """

        w = input_shape[1]
        h = input_shape[0]
        return bbox[1] * w, bbox[0] * h, bbox[3] * w, bbox[2] * h
