from typing import Any, Union

from darcyai.config_registry import ConfigRegistry
from darcyai.configurable import Configurable
from darcyai.event_emitter import EventEmitter
from darcyai.utils import validate_not_none, validate_type


class Perceptor(Configurable, EventEmitter):
    """
    The Perceptor class is the base class for all perceptors.

    # Arguments
    model_path (str): The path to the model file.

    # Examples
    ```python
    >>> from darcyai.perceptor import Perceptor
    >>> class MyPerceptor(Perceptor):
    >>>     def __init__(self):
    ...         Perceptor.__init__(self, "path/to/model")

    >>>     def run(self, input_data):
    ...         return input_data.data

    >>>     def load(self):
    ...         pass
    ```
    """

    def __init__(self, model_path: str, **kwargs):
        Configurable.__init__(self, **kwargs)
        EventEmitter.__init__(self, **kwargs)

        validate_not_none(model_path, "model_path is required")

        self.model_path = model_path

        self.__loaded = False
        self.__config_registry = None

    def run(self, input_data: Any, config: ConfigRegistry = None) -> Any:
        """
        Runs the perceptor on the input data.

        # Arguments
        input_data (StreamData): The input data to run the perceptor on.
        config (ConfigRegistry): The configuration for the perceptor. Defaults to `None`.

        # Returns
        Any: The output of the perceptor.
        """
        raise NotImplementedError("Perceptor.run() is not implemented")

    def load(self, accelerator_idx: Union[int, None] = None) -> None:
        """
        Loads the perceptor.

        # Arguments
        accelerator_idx (int, None): The index of the accelerator to load
            the perceptor on. Defaults to `None`.
        """
        raise NotImplementedError("Perceptor.load() is not implemented")

    def is_loaded(self) -> bool:
        """
        Checks if the perceptor is loaded.

        # Returns
        bool: True if the perceptor is loaded, False otherwise.
        """
        return self.__loaded

    def set_loaded(self, loaded: bool) -> None:
        """
        Sets the perceptor loaded state.

        # Arguments
        loaded (bool): The loaded state.
        """
        validate_not_none(loaded, "loaded is required")
        validate_type(loaded, bool, "loaded must be a boolean")

        self.__loaded = loaded

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
