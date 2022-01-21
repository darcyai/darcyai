from typing import List

from darcyai.config import Config


class Configurable():
    """
    Base class for all configurable objects.
    """

    def __init__(self):
        self.config_schema = []

    def get_config_schema(self) -> List[Config]:
        """
        Gets the keys of the config.

        # Returns
        List[Config]: The config schema.
        """
        return self.config_schema
