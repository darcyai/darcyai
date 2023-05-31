import gi
import time
from threading import Thread
from typing import Any, Callable

from darcyai.log import setup_custom_logger
from darcyai.output.output_stream import OutputStream
from darcyai.utils import validate_not_none, validate_type, validate

gi.require_version("Gst", "1.0")
gi.require_version("GstRtspServer", "1.0")
# pylint: disable=wrong-import-position
from gi.repository import Gst, GstRtspServer, GLib


class RtspServer(OutputStream):
    """
    RTSP Server
    """

    def __init__(self,
                 path: str = "/_feed",
                 port: int = 8554,
                 host: str = "0.0.0.0",
                 fps: int = 20,
                 width: int = 640,
                 height: int = 480,
                 resize_callback: Callable[[Any], Any] = None,
                 **kwargs):
        super().__init__(**kwargs)

        validate_not_none(path, "path is required")
        validate_type(path, str, "path must be a string")
        self.__path = path if path.startswith("/") else "/" + path

        validate_not_none(port, "port is required")
        validate_type(port, int, "port must be an integer")
        validate(0 <= port <= 65535, "port must be between 0 and 65535")
        self.__port = port

        validate_not_none(host, "host is required")
        validate_type(host, str, "host must be a string")
        self.__host = host

        validate_not_none(fps, "fps is required")
        validate_type(fps, int, "fps must be an integer")
        validate(fps > 0, "fps must be greater than 0")
        self.__fps = fps

        if resize_callback is not None:
            validate_type(resize_callback, Callable,
                          "resize_callback must be a callable")
        self.__resize_callback = resize_callback

        validate_not_none(width, "width is required")
        validate_type(width, int, "width must be an integer")
        validate(width > 0, "width must be greater than 0")
        self.__width = width

        validate_not_none(height, "height is required")
        validate_type(height, int, "height must be an integer")
        validate(height > 0, "height must be greater than 0")
        self.__height = height

        self.__logger = setup_custom_logger(__name__)
        self.__latest_frame = None

        self.__logger.debug("Starting RTSP Server")
        Gst.init(None)
        self.__server = None
        self.__create_and_start_server()

        self.__logger.debug("Starting the main loop")
        loop = GLib.MainLoop()
        t = Thread(target=loop.run)
        t.daemon = True
        t.start()

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
        >>>                                   fps=20,
        >>>                                   quality=100)
        >>> live_feed_stream.write(frame)
        ```
        """
        if data is None:
            return

        frame = data.copy()
        if self.__resize_callback is not None:
            frame = self.__resize_callback(frame)

        self.__latest_frame = frame

    def close(self) -> None:
        pass

    def __get_latest_frame(self):
        return self.__latest_frame

    def __create_and_start_server(self):
        self.__server = GstServer(path=self.__path,
                                  port=self.__port,
                                  host=self.__host,
                                  fps=self.__fps,
                                  width=self.__width,
                                  height=self.__height,
                                  get_frame=self.__get_latest_frame)
        self.__server.start()


class SensorFactory(GstRtspServer.RTSPMediaFactory):
    """RTSP Media Factory for streaming sensor data"""

    def __init__(self, height, width, fps, get_frame, **properties):
        super().__init__(**properties)
        self.number_frames = 0
        self.fps = fps
        self.get_frame = get_frame
        self.duration = 1 / self.fps * Gst.SECOND  # duration of a frame in nanoseconds
        self.launch_string = "appsrc name=source is-live=true block=true format=GST_FORMAT_TIME " \
                             f"caps=video/x-raw,format=BGR,width={width},height={height}, " \
                             f"framerate={fps}/1 ! videoconvert ! video/x-raw,format=I420 " \
                             "! x264enc speed-preset=ultrafast tune=zerolatency threads=4 " \
                             "! rtph264pay config-interval=1 name=pay0 pt=96"

    def on_need_data(self, src, _):
        """Callback for when new data is needed"""
        frame = self.get_frame()
        if frame is None:
            return

        data = frame.tobytes()
        buf = Gst.Buffer.new_allocate(None, len(data), None)
        buf.fill(0, data)
        buf.duration = self.duration
        timestamp = self.number_frames * self.duration
        buf.pts = buf.dts = int(timestamp)
        buf.offset = timestamp
        self.number_frames += 1
        retval = src.emit("push-buffer", buf)
        if retval != Gst.FlowReturn.OK:
            print(retval)

    def do_create_element(self, _):
        return Gst.parse_launch(self.launch_string)

    def do_configure(self, rtsp_media):
        self.number_frames = 0
        appsrc = rtsp_media.get_element().get_child_by_name("source")
        appsrc.connect("need-data", self.on_need_data)


class GstServer(GstRtspServer.RTSPServer):
    """Gstreamer RTSP Server"""

    def __init__(self,
                 port: int,
                 host: str,
                 path: str,
                 height: int,
                 width: int,
                 fps: int,
                 get_frame: Callable,
                 **properties):
        super().__init__(**properties)
        self.factory = SensorFactory(height, width, fps, get_frame)
        self.factory.set_shared(True)
        self.get_mount_points().add_factory(path, self.factory)
        self.set_address(host)
        self.set_service(str(port))
        self.attach(None)
        self.name = path
        self.__stop = False

    def start(self):
        # start the thread
        t = Thread(target=self.update, name=self.name, args=())
        t.daemon = True
        t.start()

        return self

    def update(self):
        while True:
            if self.__stop:
                break
            else:
                time.sleep(self.factory.duration / Gst.SECOND)

    def stop(self):
        self.__stop = True
