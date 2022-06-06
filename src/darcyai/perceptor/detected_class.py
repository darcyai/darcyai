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

class Class:
    """
    Class to store detected class information.

    # Arguments
    class_id (int): The class ID.
    name (str): The class name.
    confidence (float): The confidence of the class.
    """

    def __init__(self, class_id, name, confidence):
        self.class_id = class_id
        self.name = name
        self.confidence = confidence

    def __str__(self):
        """
        Returns a string representation of the class.

        # Returns
        str: The string representation of the class.
        """
        return f"Class(class_id={self.class_id}, name={self.name}, confidence={self.confidence})"
