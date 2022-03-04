import cv2
import threading
import time
from typing import Iterable

from darcyai.input.input_stream import InputStream
from darcyai.input.video_stream_data import VideoStreamData
from darcyai.utils import validate_not_none, timestamp, validate_type


class VideoFileStream(InputStream):
    """
    An input stream that reads frames from a video file.

    # Arguments
    file_name (str): The name of the video file to stream.
    use_pi_camera (bool): Whether or not to use the Raspberry Pi camera.
    loop (bool): Whether or not to loop the video. Defaults to `True`.
    process_all_frames (bool): Whether or not to process all frames. Defaults to `True`.

    # Examples
    ```python
    >>> from darcyai.input.video_file_stream import VideoFileStream
    >>> video_file_stream = VideoFileStream(file_name="video.mp4",
                                            loop=True,
                                            process_all_frames=True)
    ```
    """

    def __init__(self, file_name: str, loop: bool = True, process_all_frames: bool = True):
        super().__init__()

        validate_not_none(file_name, "file_name is required")
        validate_type(file_name, str, "file_name must be a string")

        self.__file_name = file_name
        self.__loop = loop
        self.__process_all_frames = process_all_frames

        self.__frame_number = 0
        self.__vs = None
        self.__stopped = True
        self.__lock = threading.Lock()

    def stop(self) -> None:
        """
        Stops the video stream.

        # Examples
        ```python
        >>> from darcyai.input.video_file_stream import VideoFileStream
        >>> video_file_stream = VideoFileStream(file_name="video.mp4",
                                                loop=True,
                                                process_all_frames=True)
        >>> video_file_stream.stop()
        ```
        """
        self.__stopped = True

        if self.__vs is None:
            return

        with self.__lock:
            self.__vs.release()
            self.__vs = None
            self.__frame_number = 0

    def stream(self) -> Iterable[VideoStreamData]:
        """
        Streams the video frames.

        # Returns
        An iterable of VideoStreamData objects.

        # Examples
        ```python
        >>> from darcyai.input.video_file_stream import VideoFileStream
        >>> video_file_stream = VideoFileStream(file_name="video.mp4",
                                                loop=True,
                                                process_all_frames=True)
        >>> video_file_stream.stream()
        ```
        """
        if self.__stopped or self.__vs is None:
            self.__vs = self.__initialize_video_file_stream()

        if not self.__vs.isOpened():
            # TODO
            pass

        self.__total_frames = self.__vs.get(cv2.CAP_PROP_FRAME_COUNT)

        if not self.__process_all_frames:
            self.__rate = self.__vs.get(cv2.CAP_PROP_FPS)
            self.__delay = int(1000 / self.__rate)
            self.__last_frame_timestamp = None

        self.__stopped = False

        self.__frame_number = 0
        while not self.__stopped and self.__vs.isOpened():
            with self.__lock:
                if self.__stopped:
                    break

                success, frame = self.__get_next_frame()
                if not success:
                    break

                yield(VideoStreamData(frame, timestamp()))

    def __initialize_video_file_stream(self) -> cv2.VideoCapture:
        cap = cv2.VideoCapture(self.__file_name)

        if not cap.isOpened():
            raise Exception(f"Cannot open {self.__file_name}")

        return cap

    def __get_next_frame(self):
        """
        Gets the next frame from the video file.

        # Returns
        A tuple of (success, frame).
        """
        if self.__vs is None:
            return False, None

        if not self.__process_all_frames:
            if self.__last_frame_timestamp is None:
                self.__last_frame_timestamp = timestamp()
            else:
                now = timestamp()
                diff = now - self.__last_frame_timestamp
                if diff < self.__delay:
                    time.sleep((self.__delay - diff) / 1000)
                else:
                    self.__frame_number = self.__frame_number + int(diff / self.__delay)
                    if self.__frame_number >= self.__total_frames:
                        if self.__loop:
                            self.__frame_number = 0
                        else:
                            return False, None

                    self.__vs.set(cv2.CAP_PROP_POS_FRAMES, self.__frame_number)

                self.__last_frame_timestamp = now

        success, frame = self.__vs.read()

        if not success:
            return False, None

        self.__frame_number += 1

        if self.__frame_number >= self.__total_frames:
            if self.__loop:
                self.__vs.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.__frame_number = 0
            else:
                return False, None

        return True, frame
