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

from typing import Any


class ConfigRegistry():
    """
    This class is used to represent the perceptor configuration.
    """

    def __init__(self):
        self.__dict__ = {}

    def set_value(self, key: str, value: Any) -> None:
        """
        Set the value of a key in the config.

        # Arguments
        key (str): The key to set.
        value (Any): The value to set.
        """
        self.__dict__[key] = value

    def get(self, key: str) -> Any:
        """
        Get the value of a key in the config.

        # Arguments
        key (str): The key to get.

        # Returns
        Any: The value of the key.
        """
        return self.__dict__[key]

    def serialize(self) -> dict:
        """
        Serialize the config to a dictionary.

        # Returns
        dict: The serialized config.
        """
        return self.__dict__
