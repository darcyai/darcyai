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

class Object:
    """
    Class for storing detected objects.

    # Arguments
    class_id (int): The class ID.
    name (str): The class name.
    confidence (float): The confidence of the class.
    xmin (int): The x-coordinate of the top left corner of the bounding box.
    ymin (int): The y-coordinate of the top left corner of the bounding box.
    xmax (int): The x-coordinate of the bottom right corner of the bounding box.
    ymax (int): The y-coordinate of the bottom right corner of the bounding box.
    """

    def __init__(self, class_id, name, confidence, xmin, ymin, xmax, ymax):
        self.class_id = class_id
        self.name = name
        self.confidence = confidence
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

    def __str__(self):
        """
        Returns a string representation of the class.

        # Returns
        str: The string representation of the class.
        """
        return f"Object(class_id={self.class_id}, name={self.name}, confidence={self.confidence},\
            xmin={self.xmin}, ymin={self.ymin}, xmax={self.xmax}, ymax={self.ymax})"
