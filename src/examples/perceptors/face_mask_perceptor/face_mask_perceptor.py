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

#Add libraries we need
import os
import pathlib
from typing import Any

#Add Darcy AI libraries we need, particularly the ImageClassificationPerceptor base class and the Config and ConfigRegistry classes
from darcyai.perceptor.image_classification_perceptor import ImageClassificationPerceptor
from darcyai.perceptor.processor import Processor
from darcyai.config import Config
from darcyai.config_registry import ConfigRegistry
from darcyai.utils import validate_not_none, validate_type, validate

#Add our FaceMaskDetectionModel class for POM-compatible output
from face_mask_detection_model import FaceMaskDetectionModel


#Define our custom Perceptor class called "FaceMaskPerceptor"
class FaceMaskPerceptor(ImageClassificationPerceptor):
    """
    This class is a subclass of ImageClassificationPerceptor.
    It is used to detect face mask in an image.
    """

    #Define our "init" method
    def __init__(self, threshold:float=0.95):
        #Get the directory of the code file and find the AI model file
        script_dir = pathlib.Path(__file__).parent.absolute()
        coral_model_file = os.path.join(script_dir, "face_mask_detection_coral.tflite")
        cpu_model_file = os.path.join(script_dir, "face_mask_detection_cpu.tflite")

        #Set up our own text labels for AI output so we don't need a labels.txt file
        labels = {
            0: "No Mask",
            1: "Mask",
        }

        #Validate input parameters
        validate_not_none(threshold, "threshold is required")
        validate_type(threshold, (float, int), "threshold must be a number")
        validate(0 <= threshold <= 1, "threshold must be a number between 0 and 1")

        #Call "init" on the parent class and pass our AI model information
        super().__init__(processor_preference={
                             Processor.CORAL_EDGE_TPU: {
                                 "model_path": coral_model_file,
                                 "labels": labels,
                             },
                             Processor.CPU: {
                                 "model_path": cpu_model_file,
                                 "labels": labels,
                             },
                         },
                         threshold=0,
                         top_k=2)

        #Add a configuration item to the list, in this case a threshold setting that is a floating point value
        #This will show up in the configuration REST API
        self.set_config_schema([
            Config("threshold", "Threshold", "float", threshold, "Threshold"),
        ])


    #Define our "run" method
    def run(self, input_data:Any, config:ConfigRegistry=None) -> FaceMaskDetectionModel:
        """
        This function is used to run the face mask detection.

        Arguments:
            input_data (Any): RGB array of the face.
            config (ConfigRegistry): The configuration.

        Returns:
            FaceMaskDetectionModel: The face mask detection model.
        """
        #Get the AI model result by calling "run" on the parent class where we have already passed our AI model
        perception_result = super().run(input_data=input_data, config=config)

        #Check the output to see if the mask detection crosses the configured threshold
        has_mask = False
        if len(perception_result) > 0:
            try:
                idx = [i for i, x in enumerate(perception_result) if x.name == 'Mask']
                if len(idx) > 0:
                    threshold = self.get_config_value("threshold") / 100
                    has_mask = bool(perception_result[idx[0]].confidence >= threshold)
            except:
                has_mask = False

        #Wrap the result in the POM-compatible class and send it out
        return FaceMaskDetectionModel(has_mask)
