# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

import time
from darcyai.input.input_stream import InputStream
from darcyai.stream_data import StreamData
from darcyai.utils import timestamp

class SampleInputStream(InputStream):
    def __init__(self,):
        self.__stopped = True


    def stop(self):
        self.__stopped = True


    def stream(self):
        self.__stopped = False

        while not self.__stopped:
            time.sleep(1)

            yield(StreamData("Hello!", timestamp()))
