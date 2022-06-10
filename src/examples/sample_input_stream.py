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

import time
from darcyai.input.input_stream import InputStream
from darcyai.stream_data import StreamData
from darcyai.utils import timestamp


class SampleInputStream(InputStream):
    """
    This is a sample input stream.
    """

    def __init__(self,):
        super().__init__()
        self.__stopped = True

    def stop(self):
        self.__stopped = True

    def stream(self):
        self.__stopped = False

        while not self.__stopped:
            time.sleep(1)

            yield(StreamData("Hello!", timestamp()))
