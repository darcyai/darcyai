import json

from darcyai.file_stream import FileStream
from darcyai.output.output_stream import OutputStream
from darcyai.utils import validate_not_none, validate_type


class JSONOutputStream(OutputStream):
    """
    OutputStream implementation that writes to a JSON file.

    # Arguments
    file_path (str): The path to the JSON file to write to.
    buffer_size (int): The size of the buffer to use when writing to the
        JSON file. Defaults to `0`.
    flush_interval (int): The number of seconds before flushing the buffer
        to disk. Defaults to `0`.

    # Examples
    ```python
    >>> from darcyai.output.json_output_stream import JSONOutputStream
    >>> json_output_stream = JSONOutputStream(file_path="output.csv",
                                              buffer_size=0)
    ```
    """

    def __init__(self,
                 file_path: str,
                 buffer_size: int = 0,
                 flush_interval: int = 0) -> None:
        super().__init__()

        validate_not_none(file_path, "file_path is required")
        validate_type(file_path, str, "file_path must be a string")

        self.__file_stream = FileStream(
            file_path,
            buffer_size=buffer_size,
            flush_interval=flush_interval)

        self.config_schema = []

    def write(self, data: dict) -> None:
        """
        Writes the given data to the JSON file.

        # Arguments
        data (dict): The data to write to the JSON file.

        # Examples
        ```python
        >>> from darcyai.output.json_output_stream import JSONOutputStream
        >>> json_output_stream = JSONOutputStream(file_path="output.csv",
                                                  buffer_size=0)
        >>> json_output_stream.write({"key": "value"})
        ```
        """
        if data is None:
            return

        validate_type(data, dict, "data must be a dictionary")

        self.__file_stream.write_string(json.dumps(data))

    def close(self) -> None:
        """
        Closes the JSON file.

        # Examples
        ```python
        >>> from darcyai.output.json_output_stream import JSONOutputStream
        >>> json_output_stream = JSONOutputStream(file_path="output.csv",
                                                  buffer_size=0)
        >>> json_output_stream.close()
        ```
        """
        self.__file_stream.close()
