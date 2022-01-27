import cv2
from importlib import import_module
from typing import Any, List

from darcyai.config_registry import ConfigRegistry
from darcyai.utils import validate_not_none, validate_type, validate

from .coral_perceptor_base import CoralPerceptorBase


class ObjectDetectionPerceptor(CoralPerceptorBase):
    """
    ObjectDetectionPerceptor is a class that implements the Perceptor interface for
    object detection.

    Arguments:
        threshold (float): The threshold for object detection.
        labels_file (str): The path to the labels file.
        **kwargs: Keyword arguments to pass to Perceptor.
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


    def run(self, input_data:Any, config:ConfigRegistry=None) -> (List[Any], List[str]):
        """
        Runs the object detection model on the input data.

        Arguments:
            input_data (Any): The input data to run the model on.
            config (ConfigRegistry): The configuration for the Perceptor.

        Returns:
            (list[Any], list(str)): A tuple containing the detected objects and the labels.
        """
        labels = []

        _, scale = self.__common.set_resized_input(
            self.interpreter,
            (input_data.shape[1], input_data.shape[0]),
            lambda size: cv2.resize(input_data, size))

        self.interpreter.invoke()

        detected_objects = self.__detect.get_objects(self.interpreter, self.__threshold, scale)

        if not self.__labels is None:
            for detected_object in detected_objects:
                labels.append(self.__labels.get(detected_object.id, detected_object.id))

        return detected_objects, labels


    def load(self, accelerator_idx:[int, None]) -> None:
        """
        Loads the object detection model.

        Arguments:
            accelerator_idx (int): The index of the Edge TPU to use.

        Returns:
            None
        """
        CoralPerceptorBase.load(self, accelerator_idx)
