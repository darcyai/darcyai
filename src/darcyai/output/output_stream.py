from typing import Any

from darcyai.configurable import Configurable
from darcyai.config_registry import ConfigRegistry
from darcyai.utils import validate_not_none, validate_type


class OutputStream(Configurable):
    """
    OutputStream is the base class that is used to write output to a stream.

    # Arguments
    ignore_none (bool): Whether or not to call the endpoint when
        the data is None. Defaults to `True`.

    # Examples
    ```python
    >>> from darcyai.output.output_stream import OutputStream

    >>> class MyOutputStream(OutputStream):
    ...     def write(self, data: dict):
    ...         print(data)

    >>>     def close(self):
    ...         pass
    ```
    """

    def __init__(self, ignore_none: bool = True, **kwargs):
        Configurable.__init__(self, **kwargs)


        validate_not_none(ignore_none, "ignore_none is required")
        validate_type(ignore_none, bool, "ignore_none must be a boolean")
        self.ignore_none = ignore_none

        self.__config_registry = None

    def write(self, data: Any) -> Any:
        """
        Processes the data and writes it to the output stream.

        # Arguments
        data (Any): The data to be written to the output stream.

        # Returns
        Any: The data that was written to the output stream.
        """
        raise NotImplementedError("OutputStream.write() not implemented")

    def close(self) -> None:
        """
        Closes the output stream.
        """
        raise NotImplementedError("OutputStream.close() not implemented")

    def set_config_value(self, key: str, value: Any):
        """
        Sets a config value.

        # Arguments
        key (str): The key of the config.
        value (Any): The value to set.
        """
        self.init_config_registry()

        if not hasattr(self.__config_registry, key):
            return

        config = next(
            (x for x in self.get_config_schema() if x.name == key),
            None)
        if config is None:
            return

        if not config.is_valid(value):
            raise ValueError(f'Invalid value for config key "{key}": {value}')

        self.__config_registry.set_value(key, value)

    def get_config_value(self, key: str) -> Any:
        """
        Gets a config value.

        # Arguments
        key (str): The key of the config.

        # Returns
        Any: The value of the config.
        """
        self.init_config_registry()

        if not hasattr(self.__config_registry, key):
            return None

        return self.__config_registry.get(key)

    def init_config_registry(self):
        """
        Initializes the config registry.
        """
        if self.__config_registry is not None:
            return

        self.__config_registry = ConfigRegistry()
        for config in self.config_schema:
            self.__config_registry.set_value(config.name, config.default_value)
