import threading
from typing import Callable, Iterable

from darcyai.input.input_stream import InputStream
from darcyai.stream_data import StreamData
from darcyai.utils import validate_not_none, validate_type


class InputMultiStream:
    """
    A class that represents a collection of input streams.

    # Arguments
    aggregator (Callable[[None], StreamData]): a function that takes a
        list of data and returns a single data point
    callback (Callable[[StreamData], None]): a function that gets called
        when data is received from a stream

    # Examples
    ```python
    >>> from darcyai.input.input_multi_stream import InputMultiStream
    >>> from darcyai.stream_data import StreamData

    >>> def aggregator():
    ...     return StreamData("data", 1234567890)

    >>> def callback(data: StreamData):
    ...     print(data.data, data.timestamp)

    >>> input_stream = InputMultiStream(aggregator, callback)
    ```
    """

    def __init__(self,
                 aggregator: Callable[[None],
                                      StreamData],
                 callback: Callable[[StreamData],
                                    None]):
        validate_not_none(aggregator, "aggregator is required")
        validate_not_none(callback, "callback is required")

        self.__callback = callback
        self.__aggregator = aggregator

        self.__input_streams = {}
        self.__input_stream_threads = {}
        self.__stopped = True

    def remove_stream(self, name: str) -> None:
        """
        Removes a stream from the collection.

        # Arguments
        name (str): the name of the stream to remove

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.input.input_multi_stream import InputMultiStream

        >>> usb_camera = CameraStream(video_device="/dev/video0")

        >>> input_stream = InputMultiStream(aggregator, callback)
        >>> input_stream.add_stream("usb_camera", usb_camera)

        >>> input_stream.remove_stream("usb_camera")
        ```
        """
        if name not in self.__input_streams:
            return

        self.__input_streams[name].stop()
        if name in self.__input_stream_threads:
            self.__input_stream_threads.pop(name)

        self.__input_streams.pop(name)

    def get_stream(self, name: str) -> InputStream:
        """
        Gets a stream from the collection.

        # Arguments
        name (str): the name of the stream to get

        # Returns
        InputStream: the stream with the given name

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.input.input_multi_stream import InputMultiStream

        >>> usb_camera = CameraStream(video_device="/dev/video0")

        >>> input_stream = InputMultiStream(aggregator, callback)
        >>> input_stream.add_stream("usb_camera", usb_camera)

        >>> input_stream.get_stream("usb_camera")
        ```
        """
        if name not in self.__input_streams:
            return None

        return self.__input_streams[name]

    def add_stream(self, name: str, stream: InputStream) -> None:
        """
        Adds a stream to the collection.

        # Arguments
        name (str): the name of the stream to add
        stream (InputStream): the stream to add

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.input.input_multi_stream import InputMultiStream

        >>> usb_camera = CameraStream(video_device="/dev/video0")

        >>> input_stream = InputMultiStream(aggregator, callback)
        >>> input_stream.add_stream("usb_camera", usb_camera)
        ```
        """
        validate_not_none(stream, "stream is required")
        validate_type(stream, (InputStream, InputMultiStream),
                      "stream is not of type InputStream")
        if name in self.__input_streams:
            raise Exception(f"stream with name {name} already exists")

        self.__input_streams[name] = stream

        if not self.__stopped:
            self.__input_stream_threads[name] = threading.Thread(
                target=self.__start_stream, args=[name])
            self.__input_stream_threads[name].start()

    def stream(self) -> Iterable[StreamData]:
        """
        Starts streaming data from all streams in the collection.

        # Returns
        Iterable[StreamData]: an iterable of data from all streams

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.input.input_multi_stream import InputMultiStream

        >>> usb_camera = CameraStream(video_device="/dev/video0")

        >>> input_stream = InputMultiStream(aggregator, callback)
        >>> input_stream.add_stream("usb_camera", usb_camera)

        >>> input_stream.stream()
        ```
        """
        if len(self.__input_streams) == 0:
            raise Exception("at least 1 stream is required")

        self.__stopped = False

        for stream_name in self.__input_streams:
            self.__input_stream_threads[stream_name] = threading.Thread(
                target=self.__start_stream, args=[stream_name])
            self.__input_stream_threads[stream_name].start()

        while not self.__stopped:
            data = self.__aggregator()

            yield data

    def stop(self) -> None:
        """
        Stops streaming data from all streams in the collection.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.input.input_multi_stream import InputMultiStream

        >>> usb_camera = CameraStream(video_device="/dev/video0")

        >>> input_stream = InputMultiStream(aggregator, callback)
        >>> input_stream.add_stream("usb_camera", usb_camera)

        >>> input_stream.stop()
        ```
        """
        for stream in self.__input_streams.values():
            stream.stop()

        self.__stopped = True

    def __start_stream(self, stream_name: str) -> None:
        """
        Starts streaming data from a stream.

        # Arguments
        stream_name (str): the name of the stream to start
        """
        input_stream = self.__input_streams[stream_name]
        stream = input_stream.stream()
        validate_type(
            stream,
            Iterable,
            f"stream '{stream_name}' is not of type Iterable")

        for data in stream:
            self.__callback(stream_name, data)
