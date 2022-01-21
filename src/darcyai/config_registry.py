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
