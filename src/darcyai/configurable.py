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

from typing import List

from darcyai.config import Config


class Configurable():
    """
    Base class for all configurable objects.
    """

    def __init__(self):
        self.__config_schema = []

    def set_config_schema(self, config_schema: List[Config]) -> None:
        """
        Sets the config schema.

        # Arguments
        config_schema (list): The config schema.
        """
        self.__config_schema = config_schema

    def get_config_schema(self) -> List[Config]:
        """
        Gets the keys of the config.

        # Returns
        List[Config]: The config schema.
        """
        return self.__config_schema
