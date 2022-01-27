import cv2
import numpy as np
from importlib import import_module
from typing import Any, List

from darcyai.config_registry import ConfigRegistry
from darcyai.utils import validate_not_none, validate_type, validate

from .coral_perceptor_base import CoralPerceptorBase


class ImageClassificationPerceptor(CoralPerceptorBase):
    """
    ImageClassificationPerceptor is a class that implements the Perceptor interface for
    image classification.

    Arguments:
        threshold (float): The threshold for object detection.
        top_k (int): The number of top predictions to return.
        labels_file (str): The path to the labels file.
        labels (dict): A dictionary of labels.
        mean (float): The mean of the image.
        std (float): The standard deviation of the image.
        **kwargs: Keyword arguments to pass to Perceptor.
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


    def run(self, input_data:Any, config:ConfigRegistry=None) -> (List[Any], List[str]):
        """
        Runs the image classification model.

        Arguments:
            input_data (Any): The input data to run the model on.
            config (ConfigRegistry): The configuration for the perceptor.

        Returns:
            (list[Any], list(str)): A tuple containing the detected classes and the labels.
        """
        labels = []
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

        if not self.__labels is None:
            for detected_object in detected_classes:
                labels.append(self.__labels.get(detected_object.id, detected_object.id))

        return detected_classes, labels


    def load(self, accelerator_idx:[int, None]) -> None:
        """
        Loads the image classification model.

        Arguments:
            accelerator_idx (int): The index of the Edge TPU to use.

        Returns:
            None
        """
        CoralPerceptorBase.load(self, accelerator_idx)

        input_shape = self.interpreter.get_input_details()[0]["shape"]
        self.__inference_shape = (input_shape[2], input_shape[1])
