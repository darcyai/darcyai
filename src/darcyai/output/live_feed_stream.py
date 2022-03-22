import cv2
import numpy as np
import threading
import time
from datetime import datetime
from flask import Flask, Response
from typing import Any

from darcyai.log import setup_custom_logger
from darcyai.output.output_stream import OutputStream
from darcyai.config import Config
from darcyai.utils import validate_not_none, validate_type, validate


class LiveFeedStream(OutputStream):
    """
    An output stream that streams the frames.

    # Arguments
    path (str): Path to host the live stream.
    flask_app (Flask): Flask app to host the live stream. Defaults to `None`.
    port (int): Port to host the live stream. Defaults to `None`.
    host (str): Host to host the live stream. Defaults to `None`.
    fps (int): Frames per second to stream. Defaults to `20`.
    quality (int): Quality of the JPEG encoding. Defaults to `100`.

    # Examples
    ```python
    >>> from darcyai.output.live_feed_stream import LiveFeedStream
    >>> live_feed_stream = LiveFeedStream(path="/live-feed",
    >>>                                   port=8080,
    >>>                                   host="0.0.0.0",
    >>>                                   fps=20,
    >>>                                   quality=100)
    ```
    """

    def __init__(self,
                 path: str,
                 flask_app: Flask = None,
                 port: int = None,
                 host: str = None,
                 fps: int = 20,
                 quality: int = 100,
                 **kwargs):
        super().__init__(**kwargs)

        if flask_app is not None:
            validate_type(flask_app, Flask, "flask_app must be of type Flask")
        else:
            validate_not_none(port, "port is required")
            validate_type(port, int, "port must be of type int")
            validate(
                0 <= port <= 65535,
                "port must be between 0 and 65535")

            validate_not_none(host, "host is required")
            validate_type(host, str, "host must be a string")

        validate_not_none(path, "path is required")
        validate_type(path, str, "path must be a string")

        self.__validate_fps(fps)

        self.__validate_quality(quality)

        self.__flask_app = flask_app
        self.__port = port
        self.__host = host
        self.__path = path

        self.__fps = fps
        self.__quality = quality

        self.__latest_frame = None
        self.__encoded_frame = None
        self.__logger = setup_custom_logger(__name__)

        threading.Thread(target=self.__start_api_server).start()

        self.config_schema = [
            Config(
                "show_timestamp",
                "bool",
                True,
                "Show timestamp"),
            Config(
                "timestamp_format",
                "str",
                "%A %d %B %Y %I:%M:%S %p %f",
                "Timestamp format"),
        ]

    def write(self, data: Any) -> Any:
        """
        Write a frame to the stream.

        # Arguments
        data (Any): Frame to write.

        # Returns
        Any: The annotated frame.

        # Examples
        ```python
        >>> from darcyai.output.live_feed_stream import LiveFeedStream
        >>> live_feed_stream = LiveFeedStream(path="/live-feed",
        >>>                                   port=8080,
        >>>                                   host="0.0.0.0",
        >>>                                   fps=20,
        >>>                                   quality=100)
        >>> live_feed_stream.write(frame)
        ```
        """
        if data is None:
            return

        show_timestamp = self.get_config_value("show_timestamp")
        if not show_timestamp:
            frame_copy = data
        else:
            frame_copy = data.copy()

            timestamp_format = self.get_config_value("timestamp_format")
            timestamp = datetime.now()
            ts = timestamp.strftime(timestamp_format)

            ts_x = 0
            ts_y = 0
            (_, _), stamp_baseline = cv2.getTextSize(
                ts, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            ts_y = int(data.shape[0] - stamp_baseline)

            cv2.putText(frame_copy, ts, (ts_x, ts_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

        self.__latest_frame = frame_copy
        self.__encoded_frame = self.__encode_jpeg(frame_copy)

        return self.__encoded_frame

    def get_fps(self) -> int:
        """
        Get the frames per second.

        # Returns
        int: Frames per second.

        # Examples
        ```python
        >>> from darcyai.output.live_feed_stream import LiveFeedStream
        >>> live_feed_stream = LiveFeedStream(path="/live-feed",
        >>>                                   port=8080,
        >>>                                   host="0.0.0.0",
        >>>                                   fps=20,
        >>>                                   quality=100)
        >>> live_feed_stream.get_fps()
        ```
        """
        return self.__fps

    def set_fps(self, fps: int) -> None:
        """
        Set the frames per second.

        # Arguments
        fps (int): Frames per second.

        # Examples
        ```python
        >>> from darcyai.output.live_feed_stream import LiveFeedStream
        >>> live_feed_stream = LiveFeedStream(path="/live-feed",
        >>>                                   port=8080,
        >>>                                   host="0.0.0.0",
        >>>                                   fps=20,
        >>>                                   quality=100)
        >>> live_feed_stream.set_fps(30)
        ```
        """
        validate_not_none(fps, "fps must be a positive integer")
        validate_type(fps, int, "fps must be a positive integer")
        validate(fps > 0, "fps must be greater than 0")

        self.__fps = fps

    def get_quality(self) -> int:
        """
        Get the quality of the JPEG encoding.

        # Returns
        int: Quality of the JPEG encoding.

        # Examples
        ```python
        >>> from darcyai.output.live_feed_stream import LiveFeedStream
        >>> live_feed_stream = LiveFeedStream(path="/live-feed",
        >>>                                   port=8080,
        >>>                                   host="0.0.0.0",
        >>>                                   fps=20,
        >>>                                   quality=100)
        >>> live_feed_stream.get_quality()
        ```
        """
        return self.__quality

    def set_quality(self, quality: int) -> None:
        """
        Set the quality of the JPEG encoding.

        # Arguments
        quality (int): Quality of the JPEG encoding.

        # Examples
        ```python
        >>> from darcyai.output.live_feed_stream import LiveFeedStream
        >>> live_feed_stream = LiveFeedStream(path="/live-feed",
        >>>                                   port=8080,
        >>>                                   host="0.0.0.0",
        >>>                                   fps=20,
        >>>                                   quality=100)
        >>> live_feed_stream.set_quality(50)
        ```
        """
        self.__validate_quality(quality)

        self.__quality = quality

    def close(self) -> None:
        """
        Close the stream.

        # Examples
        ```python
        >>> from darcyai.output.live_feed_stream import LiveFeedStream
        >>> live_feed_stream = LiveFeedStream(path="/live-feed",
        >>>                                   port=8080,
        >>>                                   host="0.0.0.0",
        >>>                                   fps=20,
        >>>                                   quality=100)
        >>> live_feed_stream.close()
        ```
        """
        pass

    def get_latest_frame(self) -> Any:
        """
        Returns the latest frame in JPEG format.

        # Returns
        Any: Latest frame.

        # Examples
        ```python
        >>> from darcyai.output.live_feed_stream import LiveFeedStream
        >>> live_feed_stream = LiveFeedStream(path="/live-feed",
        >>>                                   port=8080,
        >>>                                   host="0.0.0.0",
        >>>                                   fps=20,
        >>>                                   quality=100)
        >>> live_feed_stream.get_latest_frame()
        ```
        """
        return self.__encoded_frame

    def __validate_fps(self, fps):
        validate_not_none(fps, "fps must be a positive integer")
        validate_type(fps, int, "fps must be a positive integer")
        validate(fps > 0, "fps must be greater than 0")

    def __validate_quality(self, quality):
        validate_not_none(quality, "quality must be a positive integer")
        validate_type(quality, int, "quality must be a positive integer")
        validate(
            0 <= quality <= 100,
            "quality must be between 0 and 100")

    def __start_api_server(self) -> None:
        """
        Start the API server.
        """
        if self.__flask_app is None:
            self.__flask_app = Flask(__name__)
            ssl_context = None
            self.__flask_app.add_url_rule(
                self.__path, self.__path, self.__live_feed)
            self.__flask_app.run(
                host=self.__host,
                port=self.__port,
                ssl_context=ssl_context,
                debug=False)
        else:
            for rule in self.__flask_app.url_map.iter_rules():
                if rule.rule == self.__path:
                    return

            self.__flask_app.add_url_rule(
                self.__path, self.__path, self.__live_feed)

    def __generate_stream(self) -> bytes:
        """
        Generate the stream.

        # Returns
        bytes: Stream.
        """
        while True:
            try:
                while self.__latest_frame is None:
                    time.sleep(0.10)
                    continue

                time.sleep(1.0 / self.__fps)
                frame = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + \
                    self.__encoded_frame
                yield frame
            except GeneratorExit:
                break
            except Exception:
                self.__logger.exception("Error at generating stream")
                pass

    def __live_feed(self) -> Response:
        """
        Live feed.

        # Returns
        Response: Multipart response object.
        """
        response = Response(
            self.__generate_stream(),
            mimetype="multipart/x-mixed-replace; boundary=frame")

        return response

    def __encode_jpeg(self, frame) -> bytes:
        """
        Encode a frame as JPEG.

        # Arguments
        frame (numpy.ndarray): Frame to encode.

        # Returns
        bytes: Encoded JPEG.
        """
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.__quality]
        img_encode = cv2.imencode(".jpg", frame, encode_param)[1]
        data_encode = np.array(img_encode)
        return data_encode.tobytes()
