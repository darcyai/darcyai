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

from darcyai.input.video_file_stream import VideoFileStream
from darcyai.utils import validate_not_none, validate_type


class RTSPStream(VideoFileStream):
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
        super().__init__(file_name=url, loop=False, process_all_frames=True)
