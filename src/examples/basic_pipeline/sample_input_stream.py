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

#Add the DarcyAI components that we need, particularly the InputStream and StreamData
import time
from darcyai.input.input_stream import InputStream
from darcyai.stream_data import StreamData
from darcyai.utils import timestamp

#Define our own InputStream class
class SampleInputStream(InputStream):
    def __init__(self,):
    	#Default to "stopped"
        self.__stopped = True

    #Define our "stop" method
    def stop(self):
        self.__stopped = True

    #Define our "stream" method which allows the data to flow
    def stream(self):
        self.__stopped = False

        #Make a simple loop that pauses for one second and then sends a string as data
        while not self.__stopped:
            time.sleep(1)

            yield(StreamData("Hello!", timestamp()))
