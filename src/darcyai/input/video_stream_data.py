import base64
import cv2

from darcyai.stream_data import StreamData


class VideoStreamData(StreamData):
    """
    StreamData representation of video frames
    """
    def serialize(self) -> dict:
        """
        Serialize the data to a dict

        # Returns
        dict: serialized data

        # Examples
        ```python
        >>> from darcyai.input.video_stream_data import VideoStreamData
        >>> data = VideoStreamData(frame, timestamp)
        >>> data.serialize()
        {
            "frame": "base64 encoded frame in jpeg format",
            "timestamp": 1638482728
        }
        ```
        """
        _, jpeg = cv2.imencode(".jpg", self.data)
        jpeg_base64 = base64.b64encode(jpeg)
        return {
            "frame": jpeg_base64,
            "timestamp": self.timestamp,
        }
