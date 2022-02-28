import cv2
import time
from imutils import video
from typing import Iterable

from darcyai.input.input_stream import InputStream
from darcyai.input.video_stream_data import VideoStreamData
from darcyai.log import setup_custom_logger
from darcyai.utils import validate_not_none, timestamp


class CameraStream(InputStream):
    """
    An input stream that gets frames from camera.

    # Arguments
    use_pi_camera (bool): Whether or not to use the Raspberry Pi camera. Defaults to `False`.
    video_device (str): The video device to use. Defaults to `None`.
    video_width (int): The width of the video frames. Defaults to `640`.
    video_height (int): The height of the video frames. Defaults to `480`.
    flip_frames (bool): Whether or not to flip the video frames. Defaults to `False`.
    fps (int): The frames per second to stream. Defaults to `30`.

    # Examples
    ```python
    >>> from darcyai.input.camera_stream import CameraStream
    >>> pi_camera = CameraStream(use_pi_camera=True)
    >>> usb_camera = CameraStream(video_device="/dev/video0")
    ```
    """

    def __init__(self,
                 use_pi_camera: bool = False,
                 video_device: str = None,
                 video_width: int = 640,
                 video_height: int = 480,
                 flip_frames: bool = False,
                 fps: int = 30):
        super().__init__()

        if not use_pi_camera:
            validate_not_none(video_device, "video_device is required")

        self.__use_pi_camera = use_pi_camera
        self.__video_device = video_device
        self.__frame_width = video_width
        self.__frame_height = video_height
        self.__flip_frames = flip_frames
        self.__fps = fps

        self.__vs = None
        self.__stopped = True

        self.__logger = setup_custom_logger(__name__)

    def stop(self) -> None:
        """
        Stops the video stream.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> usb_camera = CameraStream(video_device="/dev/video0")
        >>> usb_camera.stop()
        ```
        """
        self.__stopped = True

        if self.__vs is not None:
            self.__vs.stop()
            self.__vs = None

    def stream(self) -> Iterable[VideoStreamData]:
        """
        Streams the video frames.

        # Returns
        An iterable of VideoStreamData objects.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> usb_camera = CameraStream(video_device="/dev/video0")
        >>> usb_camera.stream()
        ```
        """
        if self.__stopped:
            self.__vs = self.__initialize_video_camera_stream()
            self.__stopped = False

        frame = self.__vs.read()
        if self.__flip_frames:
            frame = cv2.flip(frame, 1)

        yield VideoStreamData(frame, timestamp())
        if self.__vs is None:
            self.__vs = self.__initialize_video_camera_stream()

        self.__stopped = False

        while not self.__stopped:
            time.sleep(1 / self.__fps)

            if self.__stopped:
                break

            frame = self.__vs.read()

            if self.__flip_frames:
                frame = cv2.flip(frame, 1)

            yield(VideoStreamData(frame, timestamp()))

    @staticmethod
    def get_video_inputs():
        """
        Gets the available video inputs.

        # Returns
        int[]: A list of strings.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> CameraStream.get_video_inputs()
        ```
        """
        input_devices = []
        
        index = 0
        while True:
            try:
                device = cv2.VideoCapture(index)
                if not device.isOpened() or not device.read()[0]:
                    break
                input_devices.append(index)
                device.release()
            except:
                break
            index += 1

        return input_devices

    def __initialize_video_camera_stream(self) -> video.VideoStream:
        """
        Initializes the video camera stream.

        # Returns
        A video.VideoStream object.
        """
        if not self.__use_pi_camera:
            vs = video.VideoStream(
                src=self.__video_device,
                resolution=(
                    self.__frame_width,
                    self.__frame_height),
                framerate=20).start()
        else:
            vs = video.VideoStream(
                usePiCamera=True,
                resolution=(
                    self.__frame_width,
                    self.__frame_height),
                framerate=20).start()

        test_frame = vs.read()
        counter = 0
        while test_frame is None:
            if counter == 10:
                raise Exception("Could not initialize video stream")

            # Give the camera unit a few seconds to start
            self.__logger.debug("Waiting for camera unit to start...")
            counter += 1
            time.sleep(1)
            test_frame = vs.read()

        return vs
