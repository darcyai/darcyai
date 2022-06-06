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
