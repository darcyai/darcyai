# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

from typing import Any, List, Union

from darcyai.config_registry import ConfigRegistry
from darcyai.perceptor.detected_object import Object
from darcyai.perceptor.perceptor import Perceptor
from darcyai.perceptor.perceptor_utils import validate_processor_preference, get_perceptor_processor
from darcyai.perceptor.processor import Processor
from darcyai.perceptor.cpu.object_detection_perceptor import ObjectDetectionPerceptor as CpuObjectDetectionPerceptor
from darcyai.perceptor.coral.object_detection_perceptor import ObjectDetectionPerceptor as CoralObjectDetectionPerceptor


class ObjectDetectionPerceptor(Perceptor):
    """
    ObjectDetectionPerceptor is a class that implements the Perceptor interface for
    object detection.

    # Arguments
    processor_preference: A dictionary of processor preference.
        The key is the processor. Values are dictionaries of model paths and labels.
    threshold (float): The threshold for object detection.
    quantized (bool): Whether the model is quantized (CPU).

    # Example
    ```python
    from darcyai.perceptor.object_detection_perceptor import ObjectDetectionPerceptor
    from darcyai.perceptor.processor import Processor
    processor_preference = {
                               Processor.CORAL_EDGE_TPU: {
                                   "model_path": "/path/to/model.tflite",
                                   "labels_file": "/path/to/labels.txt",
                               },
                               Processor.CPU: {
                                   "model_path": "/path/to/model.tflite",
                                   "labels": {
                                       "label_1": "label_1_name",
                                       "label_2": "label_2_name",
                                   },
                               },
                           }
    object_detection_perceptor = ObjectDetectionPerceptor(processor_preference=processor_preference,
                                                          threshold=0.5,
                                                          top_k=5)
    ```
    """


    def __init__(self, processor_preference:dict, **kwargs):
        super().__init__(model_path="")

        validate_processor_preference(processor_preference)
        processor = get_perceptor_processor(list(processor_preference.keys()))
        if processor is None:
            raise Exception("No processor found")

        model_path = processor_preference[processor]["model_path"]
        if "labels_file" in processor_preference[processor]:
            labels_file = processor_preference[processor]["labels_file"]
        else:
            labels_file = None
        if "labels" in processor_preference[processor]:
            labels = processor_preference[processor]["labels"]
        else:
            labels = None

        kwargs.setdefault("labels_file", labels_file)
        kwargs.setdefault("labels", labels)

        if processor == Processor.CORAL_EDGE_TPU:
            if "quantized" in kwargs:
                del kwargs["quantized"]
            self.__perceptor = CoralObjectDetectionPerceptor(model_path=model_path,
                                                                 **kwargs)
        elif processor == Processor.CPU:
            self.__perceptor = CpuObjectDetectionPerceptor(model_path=model_path,
                                                               **kwargs)

    def run(self, input_data:Any, config:ConfigRegistry=None) -> List[Object]:
        """
        Runs the object detection model on the input data.

        # Arguments
        input_data (Any): The input data to run the model on.
        config (ConfigRegistry): The configuration for the Perceptor.

        # Returns
        list[Object]: A list of detected objects.
        """
        return self.__perceptor.run(input_data, config)

    def load(self, accelerator_idx: Union[int, None] = None) -> None:
        """
        Loads the object detection model.

        # Arguments
        accelerator_idx (int): The index of the Edge TPU to use.
        """
        return self.__perceptor.load(accelerator_idx)
