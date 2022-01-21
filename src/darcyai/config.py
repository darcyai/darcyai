from typing import Any

from darcyai.utils import validate_not_none, validate_type, validate


class Config():
    """
    Class to hold the configuration for the Perceptor.

    # Arguments
    name (str): The name of the config.
    config_type (str): The type of the config. Valid types are:
        - int
        - float
        - bool
        - str
    default_value (Any): The default value of the config.
    description (str): The description of the config.
    """

    def __init__(
            self,
            name: str,
            config_type: str,
            default_value: Any,
            description: str):
        validate_not_none(name, "name is required.")
        validate_type(name, str, "name must be a string.")
        self.name = name

        validate_not_none(config_type, "config_type is required.")
        validate_type(config_type, str, "config_type must be a string.")
        validate(config_type in ["int", "float", "bool", "str"],
                 "config_type must be one of: int, float, bool, str.")
        self.type = config_type

        validate_not_none(default_value, "default_value is required.")
        if not self.is_valid(default_value):
            raise Exception("default_value must be of type " + config_type)
        self.default_value = default_value

        validate_not_none(description, "description is required.")
        validate_type(description, str, "description must be a string.")
        self.description = description

    def is_valid(self, value: Any) -> bool:
        """
        Checks if the value is valid for the config.

        # Arguments
        value (Any): The value to check.

        # Returns
        bool: True if the value is valid, False otherwise.
        """
        if self.type == "int":
            return isinstance(value, int)
        elif self.type == "float":
            return isinstance(value, (float, int))
        elif self.type == "bool":
            return isinstance(value, bool)
        elif self.type == "str":
            return isinstance(value, str)
        else:
            return False

    def cast(self, value: Any) -> Any:
        """
        Casts the value to the type of the config.

        # Arguments
        value (Any): The value to cast.

        # Returns
        Any: The casted value.
        """
        if self.type == "int":
            return int(value)
        elif self.type == "float":
            return float(value)
        elif self.type == "bool":
            return bool(value)
        elif self.type == "str":
            return str(value)
        else:
            return value
