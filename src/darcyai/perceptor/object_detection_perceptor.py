# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

from darcyai.perceptor.multi_platform_perceptor_base import MultiPlatformPerceptorBase
from darcyai.perceptor.perceptor_utils import validate_processor_preference
from darcyai.perceptor.processor import Processor
from darcyai.perceptor.cpu.object_detection_perceptor import \
    ObjectDetectionPerceptor as CpuObjectDetectionPerceptor
from darcyai.perceptor.coral.object_detection_perceptor import \
    ObjectDetectionPerceptor as CoralObjectDetectionPerceptor


class ObjectDetectionPerceptor(MultiPlatformPerceptorBase):
    """
    ObjectDetectionPerceptor is a class that implements the Perceptor interface for
    object detection.
    """


    def __init__(self, processor_preference:dict, threshold:float, quantized:bool=True):
        """
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
        object_detection_perceptor = ObjectDetectionPerceptor(
            processor_preference=processor_preference,
            threshold=0.5,
            top_k=5)
        ```
        """
        validate_processor_preference(processor_preference)
        super().__init__(processor_preference=list(processor_preference.keys()))

        model_path = processor_preference[self.processor]["model_path"]
        if "labels_file" in processor_preference[self.processor]:
            labels_file = processor_preference[self.processor]["labels_file"]
        else:
            labels_file = None
        if "labels" in processor_preference[self.processor]:
            labels = processor_preference[self.processor]["labels"]
        else:
            labels = None

        if self.processor == Processor.CORAL_EDGE_TPU:
            self.perceptor = CoralObjectDetectionPerceptor(model_path=model_path,
                                                           threshold=threshold,
                                                           labels_file=labels_file,
                                                           labels=labels)
        elif self.processor == Processor.CPU:
            self.perceptor = CpuObjectDetectionPerceptor(model_path=model_path,
                                                         threshold=threshold,
                                                         labels_file=labels_file,
                                                         labels=labels,
                                                         quantized=quantized)
