from typing import Any, Dict, List

from darcyai.serializable import Serializable
from darcyai.stream_data import StreamData


class PerceptionObjectModel(Serializable):
    """
    This class is used to represent the perception of an object.
    """

    def __init__(self):
        super().__init__()
        self.__dict__ = {}
        self.__input_data = None
        self.__pulse_number = None
        self.__pps = 0

    def set_value(self, key: str, value: Any) -> None:
        """
        Set the value of a key in the perception object model.

        # Arguments
        key (str): The key to set.
        value (Any): The value to set.
        """
        self.__dict__[key] = value

    def get_perceptor(self, name: str) -> Any:
        """
        Get the perception result of the provided perceptor.

        # Arguments
        name (str): The name of the perceptor.

        # Returns
        Any: The result of the perception.
        """
        return self.__dict__[name]

    def get_perceptors(self) -> List[str]:
        """
        Returns list of the perceptors.

        # Returns
        List[str]: The list of the perceptors.
        """
        return list(self.__dict__.keys())

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the perception object model.

        # Returns
        `Dict[str, Any]` - The serialized perception object model.
        """
        result = {}
        for key, value in self.__dict__.items():
            if key.startswith("_PerceptionObjectModel"):
                continue

            if isinstance(value, list):
                result[key] = [self.__serialize(item) for item in value]
            else:
                result[key] = self.__serialize(value)

        if isinstance(self.__input_data, Serializable):
            result["input_data"] = self.__input_data.serialize()

        result["pulse_number"] = self.__pulse_number
        result["pps"] = self.__pps

        return result

    def set_input_data(self, input_data: StreamData) -> None:
        """
        Set the input data for the perception object model.

        # Arguments
        input_data (StreamData): The input data.
        """
        self.__input_data = input_data

    def get_input_data(self) -> StreamData:
        """
        Get the input data for the perception object model.

        # Returns
        StreamData: The input data.
        """
        return self.__input_data

    def set_pulse_number(self, pulse_number: int) -> None:
        """
        Set the pulse number for the perception object model.

        # Arguments
        pulse_number (int): The pulse number.
        """
        self.__pulse_number = pulse_number

    def get_pulse_number(self) -> int:
        """
        Get the pulse number for the perception object model.

        # Returns
        int: The pulse number.
        """
        return self.__pulse_number

    def set_pps(self, pps: int) -> None:
        """
        Set the pps for the perception object model.

        # Arguments
        pps (int): The pps.
        """
        self.__pps = pps

    def get_pps(self) -> int:
        """
        Get the pps for the perception object model.

        # Returns
        int: The pps.
        """
        return self.__pps

    def __serialize(self, value: Any) -> Any:
        """
        Serialize the value.

        # Arguments
        value (Any): The value to serialize.

        # Returns
        Any: The serialized value.
        """
        if isinstance(value, Serializable):
            return value.serialize()
        else:
            return value
