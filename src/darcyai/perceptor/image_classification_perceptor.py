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

from darcyai.perceptor.multi_platform_perceptor_base import MultiPlatformPerceptorBase
from darcyai.perceptor.perceptor_utils import validate_processor_preference
from darcyai.perceptor.processor import Processor
from darcyai.perceptor.cpu.image_classification_perceptor import \
    ImageClassificationPerceptor as CpuImageClassificationPerceptor
from darcyai.perceptor.coral.image_classification_perceptor import \
    ImageClassificationPerceptor as CoralImageClassificationPerceptor

class ImageClassificationPerceptor(MultiPlatformPerceptorBase):
    """
    ImageClassificationPerceptor is a class that implements the Perceptor interface for
    image classification.
    """

    def __init__(self,
                 processor_preference:dict,
                 threshold:float,
                 top_k:int=None,
                 mean:float=128.0,
                 std:float=128.0,
                 quantized:bool=True,
                 num_cpu_threads:int=1):
        """
        # Arguments
        processor_preference: A dictionary of processor preference.
            The key is the processor. Values are dictionaries of model paths and labels.
        threshold (float): The threshold for object detection.
        top_k (int): The number of top predictions to return.
        mean (float): The mean of the image (Coral Edge TPU).
        std (float): The standard deviation of the image (Coral Edge TPU).
        quantized (bool): Whether the model is quantized (CPU).
        num_cpu_threads (int): The number of threads to use for inference (CPU).
            Defaults to 1.

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
            self.perceptor = CoralImageClassificationPerceptor(model_path=model_path,
                                                               threshold=threshold,
                                                               top_k=top_k,
                                                               labels_file=labels_file,
                                                               labels=labels,
                                                               mean=mean,
                                                               std=std)
        elif self.processor == Processor.CPU:
            self.perceptor = CpuImageClassificationPerceptor(model_path=model_path,
                                                             threshold=threshold,
                                                             top_k=top_k,
                                                             labels_file=labels_file,
                                                             labels=labels,
                                                             quantized=quantized,
                                                             num_cpu_threads=num_cpu_threads)
