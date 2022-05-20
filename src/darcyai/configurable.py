# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

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
