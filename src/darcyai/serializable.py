from typing import Dict, Any

class Serializable:
    """
    Base class for all serializable objects.
    """

    def __init__(self):
        pass

    def serialize(self) -> Dict[str, Any]:
        """
        Serializes the object into a dictionary.

        # Returns
        `Dict[str, Any]` - The serialized object.
        """
        raise NotImplementedError("serialize() must be implemented.")
