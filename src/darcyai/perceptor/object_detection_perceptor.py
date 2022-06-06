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
from darcyai.perceptor.cpu.object_detection_perceptor import \
    ObjectDetectionPerceptor as CpuObjectDetectionPerceptor
from darcyai.perceptor.coral.object_detection_perceptor import \
    ObjectDetectionPerceptor as CoralObjectDetectionPerceptor


class ObjectDetectionPerceptor(MultiPlatformPerceptorBase):
    """
    ObjectDetectionPerceptor is a class that implements the Perceptor interface for
    object detection.
    """


    def __init__(self,
                 processor_preference:dict,
                 threshold:float,
                 quantized:bool=True,
                 num_cpu_threads:int=1):
        """
        # Arguments
        processor_preference: A dictionary of processor preference.
            The key is the processor. Values are dictionaries of model paths and labels.
        threshold (float): The threshold for object detection.
        quantized (bool): Whether the model is quantized (CPU).
        num_cpu_threads (int): The number of threads to use for inference (CPU).
            Defaults to 1.

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
                                                         quantized=quantized,
                                                         num_cpu_threads=num_cpu_threads)
