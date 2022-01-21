from typing import Any

from darcyai.serializable import Serializable


class StreamData(Serializable):
    """
    Class to hold data from a stream.

    # Arguments
    data (Any): The data to be stored.
    timestamp (int): The timestamp of the data.
    """

    def __init__(self, data: Any, timestamp: int):
        super().__init__()
        self.data = data
        self.timestamp = timestamp

    def serialize(self) -> dict:
        """
        Serializes the data.

        # Returns
        dict: The serialized data.
        """
        return {
            "data": self.data,
            "timestamp": self.timestamp
        }
