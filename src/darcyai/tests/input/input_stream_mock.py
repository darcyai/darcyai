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


class InputStreamMock(InputStream):
    """
    This class is used to mock the input stream.
    """
    def __init__(self, iter, mock=None):
        self.__iter = iter
        self.__mock = mock

    def stop(self):
        if self.__mock is not None:
            self.__mock.stop()

    def stream(self):
        for i in self.__iter:
            if self.__mock is not None:
                self.__mock.stream(i)
            yield(StreamData(i, int(time.time() * 1000)))
            time.sleep(.1)
