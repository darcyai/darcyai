from typing import Callable, Any, Union

from darcyai.log import setup_custom_logger
from darcyai.perceptor.perceptor import Perceptor
from darcyai.perception_object_model import PerceptionObjectModel
from darcyai.config_registry import ConfigRegistry
from darcyai.stream_data import StreamData
from darcyai.utils import validate_not_none, validate_type


class PerceptorNode:
    """
    PerceptorNode is a wrapper for the Perceptor object.

    # Arguments
    perceptor_name (str): The name of the perceptor
    perceptor (Perceptor): The perceptor to run
    input_callback (Callable[[StreamData, PerceptionObjectModel,
        ConfigRegistry], Any]): The callback to run on the input data. Defaults to `None`.
    output_callback (Callable[[Any, PerceptionObjectModel], Any]):
        The callback to run on the output data. Defaults to `None`.
    multi (bool): Whether or not to run the perceptor for each item in
        input data. Defaults to `False`.
    accelerator_idx (int): The index of the Edge TPU to use. Defaults to `None`.

    # Examples
    ```python
    >>> from darcyai.perceptor.perceptor_node import PerceptorNode
    >>> perceptor_node = PerceptorNode(perceptor_name="perceptor_name",
    ...                                perceptor=perceptor,
    ...                                input_callback=input_callback,
    ...                                output_callback=output_callback,
    ...                                multi=False,
    ...                                accelerator_idx=0)
    ```
    """

    def __init__(self,
                 perceptor_name: str,
                 perceptor: Perceptor,
                 input_callback: Callable[[StreamData,
                                           PerceptionObjectModel,
                                           ConfigRegistry],
                                          Any] = None,
                 output_callback: Callable[[Any,
                                            PerceptionObjectModel],
                                           Any] = None,
                 multi: bool = False,
                 accelerator_idx: Union[int, None] = None):
        validate_not_none(perceptor, "perceptor is required")
        validate_type(
            perceptor,
            Perceptor,
            "perceptor must be an instance of Perceptor")

        validate_not_none(perceptor_name, "perceptor_name is required")
        validate_type(perceptor_name, str, "perceptor_name must be a string")

        if input_callback is not None:
            validate_not_none(input_callback, "input_callback is required")
            validate_type(
                input_callback,
                Callable,
                "input_callback must be a function")

        if output_callback is not None:
            validate_type(
                output_callback,
                Callable,
                "output_callback must be a function")

        self.accelerator_idx = accelerator_idx
        self.multi = multi

        self.__name = perceptor_name
        self.__perceptor = perceptor
        self.__child_perceptors = []
        self.__input_callback = input_callback
        self.__output_callback = output_callback

        self.__logger = setup_custom_logger(f"{__name__}.{perceptor_name}")

        self.__perceptor.load(accelerator_idx)

    def add_child_perceptor(self, perceptor_name: str) -> None:
        """
        Adds a child perceptor to this perceptor

        # Arguments
        perceptor_name (str): The perceptor to add

        # Examples
        ```python
        >>> from darcyai.perceptor.perceptor_node import PerceptorNode
        >>> perceptor_node = PerceptorNode(perceptor_name="perceptor_name",
        ...                                perceptor=perceptor,
        ...                                input_callback=input_callback,
        ...                                output_callback=output_callback,
        ...                                multi=False,
        ...                                accelerator_idx=0)
        >>> perceptor_node.add_child_perceptor("child_perceptor_name")
        ```
        """
        validate_not_none(perceptor_name, "perceptor_name is required")
        validate_type(perceptor_name, str, "perceptor_name must be a string")

        self.__child_perceptors.append(perceptor_name)

    def get_child_perceptors(self) -> list:
        """
        Returns the child perceptors of this perceptor

        # Returns
        list: The child perceptors of this perceptor

        # Examples
        ```python
        >>> from darcyai.perceptor.perceptor_node import PerceptorNode
        >>> perceptor_node = PerceptorNode(perceptor_name="perceptor_name",
        ...                                perceptor=perceptor,
        ...                                input_callback=input_callback,
        ...                                output_callback=output_callback,
        ...                                multi=False,
        ...                                accelerator_idx=0)
        >>> perceptor_node.add_child_perceptor("child_perceptor_name")
        >>> perceptor_node.get_child_perceptors()
        ```
        """
        return self.__child_perceptors

    def remove_child_perceptor(self, perceptor_name: str) -> None:
        """
        Removes a child perceptor from this perceptor

        # Arguments
        perceptor_name (str): The name of the perceptor to remove

        # Examples
        ```python
        >>> from darcyai.perceptor.perceptor_node import PerceptorNode
        >>> perceptor_node = PerceptorNode(perceptor_name="perceptor_name",
        ...                                perceptor=perceptor,
        ...                                input_callback=input_callback,
        ...                                output_callback=output_callback,
        ...                                multi=False,
        ...                                accelerator_idx=0)
        >>> perceptor_node.add_child_perceptor("child_perceptor_name")
        >>> perceptor_node.remove_child_perceptor("child_perceptor_name")
        ```
        """
        if perceptor_name in self.__child_perceptors:
            self.__child_perceptors.remove(perceptor_name)

    def run(
            self,
            processed_input_data: Any,
            pom: PerceptionObjectModel,
            config: ConfigRegistry = None) -> Any:
        """
        Runs the perceptor

        # Arguments
        processed_input_data (Any): The input data to run the perceptor with.
        pom (PerceptionObjectModel): The object model to run the perceptor on.
        config (ConfigRegistry): The config registry to use. Defaults to `None`.

        # Returns
        Any: The output of the perceptor

        # Examples
        ```python
        >>> from darcyai.perceptor.perceptor_node import PerceptorNode
        >>> perceptor_node = PerceptorNode(perceptor_name="perceptor_name",
        ...                                perceptor=perceptor,
        ...                                input_callback=input_callback,
        ...                                output_callback=output_callback,
        ...                                multi=False,
        ...                                accelerator_idx=0)
        >>> perceptor_node.run(processed_input_data, pom, config)
        ```
        """
        result = self.__perceptor.run(processed_input_data, config)

        if self.__output_callback is not None:
            result = self.__output_callback(result, pom)

        self.__logger.debug("finished running %s", self.__str__())

        return result

    def set_perceptor_config(self, key: str, value: Any) -> None:
        """
        Sets the config of the perceptor

        # Arguments
        key (str): The key to set
        value (Any): The value to set

        # Examples
        ```python
        >>> from darcyai.perceptor.perceptor_node import PerceptorNode
        >>> perceptor_node = PerceptorNode(perceptor_name="perceptor_name",
        ...                                perceptor=perceptor,
        ...                                input_callback=input_callback,
        ...                                output_callback=output_callback,
        ...                                multi=False,
        ...                                accelerator_idx=0)
        >>> perceptor_node.set_perceptor_config("key", "value")
        ```
        """
        self.__perceptor.set_config_value(key, value)

    def get_perceptor_config(self, key: str) -> Any:
        """
        Gets the config of the perceptor

        # Arguments
        key (str): The key to get

        # Returns
        Any: The value of the config

        # Examples
        ```python
        >>> from darcyai.perceptor.perceptor_node import PerceptorNode
        >>> perceptor_node = PerceptorNode(perceptor_name="perceptor_name",
        ...                                perceptor=perceptor,
        ...                                input_callback=input_callback,
        ...                                output_callback=output_callback,
        ...                                multi=False,
        ...                                accelerator_idx=0)
        >>> perceptor_node.get_perceptor_config("key")
        ```
        """
        return self.__perceptor.get_config_value(key)

    def process_input_data(
            self,
            input_data: StreamData,
            pom: PerceptionObjectModel,
            config: ConfigRegistry = None) -> Any:
        """
        Processes the input data

        # Arguments
        input_data (StreamData): The input data to process input data based on.
        pom (PerceptionObjectModel): The object model to process input data based on.
        config (ConfigRegistry): The config registry to use. Defaults to `None`.

        # Returns
        Any: The processed input data

        # Examples
        ```python
        >>> from darcyai.perceptor.perceptor_node import PerceptorNode
        >>> perceptor_node = PerceptorNode(perceptor_name="perceptor_name",
        ...                                perceptor=perceptor,
        ...                                input_callback=input_callback,
        ...                                output_callback=output_callback,
        ...                                multi=False,
        ...                                accelerator_idx=0)
        >>> perceptor_node.process_input_data(input_data, pom, config)
        ```
        """
        if self.__input_callback is not None:
            return self.__input_callback(input_data, pom, config)

        return input_data.data

    def __str__(self) -> str:
        return f"PerceptorNode name: {self.__name}"
