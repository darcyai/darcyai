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

# Define a helper class for use in the Perception Object Model (POM) output
class FaceMaskDetectionModel:
    def __init__(self, has_mask: bool):
        self.__has_mask = has_mask

    def has_mask(self):
        """
        Returns:
            bool: True if the face has a mask, False otherwise.
        """
        return self.__has_mask
