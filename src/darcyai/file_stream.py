import threading

from darcyai.utils import validate_not_none, validate_type, validate

class FileStream:
    """
    A class that represents a stream of data from a file.

    # Arguments
    path: The path to the file to write to.
    append: Whether to append to the file or not. Default is False. Default is `False`.
    encoding: The encoding to use for the file. Default is "utf-8". Default is `"utf-8"`.
    buffer_size: The size of the buffer to use. Default is 1024 * 1024. Default is `1024 * 1024`.
    flush_interval: The frequency to flush the file. Default is 0 (disabled). Default is `0`.

    # Examples
    ```python
    >>> from darcyai.file_stream import FileStream
    >>> file_stream = FileStream(file_path="output.txt",
    ...                          append=True,
    ...                          encoding="utf-8",
    ...                          buffer_size=1024*1024,
    ...                          flush_interval=5)
    ```
    """
    def __init__(self,
                 path: str,
                 append: bool = False,
                 encoding: str = "utf-8",
                 buffer_size: int = 1024 * 1024,
                 flush_interval: int = 0) -> None:
        validate_not_none(path, "path is required")
        validate_type(path, str, "path must be a string")

        validate_not_none(append, "append is required")
        validate_type(append, bool, "append must be a boolean")

        validate_not_none(encoding, "encoding is required")
        validate_type(encoding, str, "encoding must be a string")
        try:
            _ = "test".encode(encoding)
        except Exception as e:
            raise ValueError(f"encoding '{encoding}' is not supported") from e

        validate_not_none(buffer_size, "buffer_size is required")
        validate_type(buffer_size, int, "buffer_size must be an integer")
        validate(buffer_size >= 0, "buffer_size must be greater than or equal to 0")

        validate_not_none(flush_interval, "flush_interval is required")
        validate_type(flush_interval, int, "flush_interval must be an integer")
        validate(flush_interval >= 0, "flush_interval must be greater than or equal to 0")

        #pylint: disable=consider-using-with
        self.__file = open(file=path,
                           mode="ab" if append else "wb",
                           buffering=buffer_size)
        self.__encoding = encoding
        self.__flush_interval = flush_interval

        self.__flush()


    def close(self):
        """
        Closes the file.

        # Examples
        ```python
        >>> from darcyai.file_stream import FileStream
        >>> file_stream = FileStream(file_path="output.txt",
        ...                          append=True,
        ...                          encoding="utf-8",
        ...                          buffer_size=1024*1024,
        ...                          flush_interval=5)
        >>> file_stream.close()
        ```
        """
        self.__file.close()

    def write_string(self, data: str) -> None:
        """
        Writes the data to the file.

        # Arguments
        data: The data to write.

        # Examples
        ```python
        >>> from darcyai.file_stream import FileStream
        >>> file_stream = FileStream(file_path="output.txt",
        ...                          append=True,
        ...                          encoding="utf-8",
        ...                          buffer_size=1024*1024,
        ...                          flush_interval=5)
        >>> file_stream.write_string("Hello World!")
        ```
        """
        self.write_bytes(data.encode(self.__encoding))

    def write_bytes(self, data: bytes) -> None:
        """
        Writes the data to the file.

        # Arguments
        data: The data to write.

        # Examples
        ```python
        >>> from darcyai.file_stream import FileStream
        >>> file_stream = FileStream(file_path="output.txt",
        ...                          append=True,
        ...                          encoding="utf-8",
        ...                          buffer_size=1024*1024,
        ...                          flush_interval=5)
        >>> file_stream.write_bytes(b"Hello World!")
        ```
        """
        self.__file.write(data)

    def __flush(self):
        """
        Flushes the file.
        """
        try:
            self.__file.flush()
        finally:
            if self.__flush_interval > 0:
                threading.Timer(interval=self.__flush_interval, function=self.__flush).start()

