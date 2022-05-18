# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

from typing import Any, List, Union

from darcyai.config_registry import ConfigRegistry
from darcyai.perceptor.detected_class import Class
from darcyai.perceptor.perceptor import Perceptor
from darcyai.perceptor.perceptor_utils import validate_processor_preference, get_perceptor_processor
from darcyai.perceptor.processor import Processor
from darcyai.perceptor.cpu.image_classification_perceptor import ImageClassificationPerceptor as CpuImageClassificationPerceptor
from darcyai.perceptor.coral.image_classification_perceptor import ImageClassificationPerceptor as CoralImageClassificationPerceptor

class ImageClassificationPerceptor(Perceptor):
    """
    ImageClassificationPerceptor is a class that implements the Perceptor interface for
    image classification.

    # Arguments
    processor_preference: A dictionary of processor preference.
        The key is the processor. Values are dictionaries of model paths and labels.
    threshold (float): The threshold for object detection.
    top_k (int): The number of top predictions to return.
    mean (float): The mean of the image (Coral Edge TPU).
    std (float): The standard deviation of the image (Coral Edge TPU).
    quantized (bool): Whether the model is quantized (CPU).

    # Example
    ```python
    from darcyai.perceptor.image_classification_perceptor import ImageClassificationPerceptor
    from darcyai.perceptor.processor import Processor
    processor_preference = {
        Processor.CORAL_EDGE_TPU: {
            "model_path": "/path/to/model.tflite",
            "labels_file": "/path/to/labels.txt", // The path to the labels file.
        },
        Processor.CPU: {
            "model_path": "/path/to/model.tflite",
            "labels": { // A dictionary of labels.
                "label_1": "label_1_name",
                "label_2": "label_2_name",
            },
        },
    }
    image_classification_perceptor = ImageClassificationPerceptor(
        processor_preference=processor_preference, threshold=0.5, top_k=5)
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
            self.__perceptor = CoralImageClassificationPerceptor(model_path=model_path,
                                                                 **kwargs)
        elif processor == Processor.CPU:
            if "mean" in kwargs:
                del kwargs["mean"]
            if "std" in kwargs:
                del kwargs["std"]
            self.__perceptor = CpuImageClassificationPerceptor(model_path=model_path,
                                                               **kwargs)

    def run(self, input_data:Any, config:ConfigRegistry=None) -> List[Class]:
        """
        Runs the image classification model.

        # Arguments
        input_data (Any): The input data to run the model on.
        config (ConfigRegistry): The configuration for the perceptor.

        # Returns
        list[Class]: A list of detected classes.
        """
        return self.__perceptor.run(input_data, config)

    def load(self, accelerator_idx: Union[int, None] = None) -> None:
        """
        Loads the image classification model.

        # Arguments
        accelerator_idx (int): The index of the Edge TPU to use.

        # Returns
        None
        """
        return self.__perceptor.load(accelerator_idx)
