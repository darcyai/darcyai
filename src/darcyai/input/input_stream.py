from typing import Iterable

from darcyai.stream_data import StreamData


class InputStream:
    """
    Base class for reading input from a stream.

    # Examples
    ```python
    >>> from darcyai.input.input_stream import InputStream
    >>> from darcyai.stream_data import StreamData

    >>> class MyInputStream(InputStream):
    ...     def stream(self):
    ...         yield StreamData("data", 1234567890)

    >>>     def stop(self):
    ...         pass
    ```
    """
    def __init__(self):
        pass

    def stream(self) -> Iterable[StreamData]:
        """
        Returns a generator that yields a stream of input.

        # Returns
        A generator that yields a stream of input.
        """
        raise NotImplementedError("InputStream.stream() not implemented")

    def stop(self) -> None:
        """
        Stops the stream.
        """
        raise NotImplementedError("InputStream.stop() not implemented")
