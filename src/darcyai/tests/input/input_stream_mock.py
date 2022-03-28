# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

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
