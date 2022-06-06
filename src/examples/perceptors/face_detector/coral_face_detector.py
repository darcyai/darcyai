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

#Add Darcy AI libraries we need, particularly the ObjectDetectionPerceptor base class and the Config and ConfigRegistry classes
from darcyai.perceptor.object_detection_perceptor import ObjectDetectionPerceptor
from darcyai.perceptor.processor import Processor
from darcyai.config import Config
from darcyai.config_registry import ConfigRegistry
from darcyai.utils import validate_not_none, validate_type, validate


#Define our custom Perceptor class called "FaceDetector"
class CoralFaceDetector(ObjectDetectionPerceptor):
    """
    Detect faces in an image.
    """

    #Define our "init" method
    def __init__(self, threshold:float=0.95):
        #Get the directory of the code file and find the AI model file
        script_dir = pathlib.Path(__file__).parent.absolute()
        model_file = os.path.join(script_dir, "ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite")

        #Validate input parameters
        validate_not_none(threshold, "threshold is required")
        validate_type(threshold, (float, int), "threshold must be a number")
        validate(0 <= threshold <= 1, "threshold must be a number between 0 and 1")

        #Call "init" on the parent class and pass our Edge TPU AI model information
        super().__init__(processor_preference={
                             Processor.CORAL_EDGE_TPU: { "model_path": model_file },
                         },
                         threshold=0)

        #Add a configuration item to the list, in this case a threshold setting that is a floating point value
        #This will show up in the configuration REST API
        self.set_config_schema([
            Config("threshold", "Threshold", "float", threshold, "Threshold"),
        ])


    #Define our "run" method
    def run(self, input_data:Any, config:ConfigRegistry=None) -> Any:
        """
        This function is used to run the face detection.

        Arguments:
            input_data (Any): RGB array of the image.
            config (ConfigRegistry): The configuration.

        Returns:
            Any: The face detection result.
        """
        #Get the AI model result by calling "run" on the parent class where we have already passed our AI model
        perception_result = super().run(input_data=input_data, config=config)

        #Create an empty result array and then fill it by checking all results against the configured threshold
        result = []
        if len(perception_result) > 0:
            for detection in perception_result:
                if detection.class_id == 0 and detection.confidence >= config.threshold:
                    result.append(detection)

        #Send out our filtered results
        return result
