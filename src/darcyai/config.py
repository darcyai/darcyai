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
        - rgb
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

        valid_types = ["int", "float", "bool", "str", "rgb"]
        validate_not_none(config_type, "config_type is required.")
        validate_type(config_type, str, "config_type must be a string.")
        validate(config_type in valid_types,
            f"config_type must be one of: {', '.join(valid_types)}.")
        self.type = config_type

        validate_not_none(default_value, "default_value is required.")
        validate(self.is_valid(default_value), f"default_value must be of type {config_type}.")
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
        elif self.type == "rgb":
            return isinstance(value, RGB)
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
        elif self.type == "rgb":
            return RGB.from_string(value)
        else:
            return value

class RGB():
    """
    Class to hold the configuration for the RGB.

    Arguments:
        red (int): The red value.
        green (int): The green value.
        blue (int): The blue value.
    """

    def __init__(self, red: int, green: int, blue: int):
        self.__red = red
        self.__green = green
        self.__blue = blue

    def red(self) -> int:
        """
        Returns the red value.

        # Returns
        int: The red value.
        """
        return self.__red

    def green(self) -> int:
        """
        Returns the green value.

        # Returns
        int: The green value.
        """
        return self.__green

    def blue(self) -> int:
        """
        Returns the blue value.

        # Returns
        int: The blue value.
        """
        return self.__blue

    def __str__(self) -> str:
        return f"{self.__red},{self.__green},{self.__blue}"

    def to_hex(self) -> str:
        """
        Returns the hex value of the RGB.

        # Returns
        str: The hex value.
        """
        return f"#{self.__red:02x}{self.__green:02x}{self.__blue:02x}"

    @staticmethod
    def from_string(rgb:str) -> "RGB":
        """
        Creates an RGB object from a comma separated RGB string.

        # Arguments
        rgb (str): The comma separated RGB string.

        # Returns
        RGB: The RGB object.

        # Examples
        ```python
        >>> RGB.from_string("255,255,255")
        ```
        """
        validate_not_none(rgb, "rgb is required.")
        validate_type(rgb, str, "rgb must be a string.")

        rgb = rgb.strip()
        validate(rgb.count(",") == 2, "rgb must be a comma separated string.")

        rgb = rgb.split(",")

        return RGB(int(rgb[0].strip()), int(rgb[1].strip()), int(rgb[2].strip()))

    @staticmethod
    def from_hex_string(hex_rgb:str) -> "RGB":
        """
        Creates an RGB object from a hex RGB string.

        # Arguments
        hex_rgb (str): The hex RGB string.

        # Returns
        RGB: The RGB object.
        """
        validate_not_none(hex_rgb, "hex_rgb is required.")
        validate_type(hex_rgb, str, "hex_rgb must be a string.")

        hex_rgb = hex_rgb.strip()
        validate(len(hex_rgb) == 7, "hex_rgb must be a hex RGB string.")
        validate(hex_rgb.startswith("#"), "hex_rgb must start with #.")

        (red, green, blue) = tuple(int(hex_rgb.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

        return RGB(red, green, blue)
