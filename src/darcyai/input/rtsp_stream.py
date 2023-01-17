# Copyright 2022 Edgeworx, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import cv2
import threading
from collections import deque
from typing import Iterable

from darcyai.input.input_stream import InputStream
from darcyai.input.video_stream_data import VideoStreamData
from darcyai.utils import validate_not_none, timestamp, validate_type


class RTSPStream(InputStream):
    """
    An input stream that gets frames from a RTSP server.

    # Arguments
    url (str): The URL of the RTSP stream.

    # Examples
    ```python
    >>> from darcyai.input.rtsp_stream import RTSPStream
    >>> rtsp = RTSPStream(url="rtsp://some.domain.com/stream")
    ```
    """

    def __init__(self,
                 url: str):
        validate_not_none(url, "url is required")
        validate_type(url, str, "url must be a string.")
        self.__url = url

        self.__vs = None
        self.__stopped = True
        self.__frame = deque(maxlen=1)
        self.__read = threading.Thread(target=self.__get_frame)

    def stop(self) -> None:
        """
        Stops the video stream.

        # Examples
        ```python
        >>> from darcyai.input.rtsp_stream import RTSPStream
        >>> rtsp_stream = RTSPStream(url="rtsp://localhost")
        >>> rtsp_stream.stop()
        ```
        """
        self.__stopped = True

        if self.__vs is None:
            return

    def stream(self) -> Iterable[VideoStreamData]:
        """
        Streams the video frames.

        # Returns
        An iterable of VideoStreamData objects.

        # Examples
        ```python
        >>> from darcyai.input.rtsp_stream import RTSPStream
        >>> rtsp_stream = RTSPStream(url="rtsp://localhost")
        >>> rtsp_stream.stream()
        ```
        """
        self.__stopped = False

        self.__read.start()

        while not self.__stopped:
            try:
                frame = self.__frame.pop()
                yield(VideoStreamData(frame, timestamp()))
            except IndexError:
                pass

        self.__vs.release()
        self.__vs = None

    def __initialize_rtsp_stream(self) -> cv2.VideoCapture:
        cap = cv2.VideoCapture(self.__url)

        if not cap.isOpened():
            raise Exception(f"Cannot open {self.__url}")

        return cap

    def __get_frame(self):
        if self.__vs is None:
            self.__vs = self.__initialize_rtsp_stream()

        if not self.__vs.isOpened():
            raise Exception(f"Cannot open {self.__url}")

        while not self.__stopped and self.__vs.isOpened():
            success, frame = self.__vs.read()
            if not success:
                continue
            self.__frame.append(frame)
