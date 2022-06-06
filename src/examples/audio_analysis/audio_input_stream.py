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

#Add libraries for audio input and math operations
import audioop
import math
import numpy as np
import pyaudio

#Add Darcy AI libraries that we need, particularly InputStream and StreamData
from darcyai.input.input_stream import InputStream
from darcyai.stream_data import StreamData
from darcyai.utils import timestamp, validate_type, validate_not_none, validate

#Define our own Darcy AI InputStream class
class AudioInputStream(InputStream):
    """
    AudioInputStream is an input stream that reads audio data from a microphone.

    # Arguments
    chunk_size: The size of the audio data chunk.
        Defaults to 1024.
    format: The format of the audio data.
        Defaults to pyaudio.paFloat32.
    sample_len_sec: The length of the audio sample in seconds.
        Defaults to 5.
    """
    def __init__(self,
                 chunk_size: int = 1024,
                 format: str = pyaudio.paFloat32,
                 sample_len_sec: int = 5):

        #Validate input parameters
        validate_not_none(chunk_size, "chunk_size must be provided")
        validate_type(chunk_size, int, "chunk_size must be an integer")
        validate(chunk_size > 0, "chunk_size must be greater than 0")
        self.__chunk_size = chunk_size

        validate_not_none(format, "format must be provided")
        validate_type(format, int, "format must be an integer")
        self.__format = format

        validate_not_none(sample_len_sec, "sample_len_sec must be provided")
        validate_type(sample_len_sec, int, "sample_len_sec must be an integer")
        validate(sample_len_sec > 0, "sample_len_sec must be greater than 0")
        self.__sample_len_sec = sample_len_sec
        
        #Set up class properties with default starting values 
        self.__audio_stream = None
        self.__stopped = True
        self.__threshold = 30000

        #Set up audio library
        self.__pyaudio = pyaudio.PyAudio()
        self.__input_device_index = self.__pyaudio.get_default_input_device_info()["index"]
        self.__channels = self.__pyaudio.get_default_input_device_info()["maxInputChannels"]
        self.__rate = int(self.__pyaudio.get_device_info_by_index(self.__input_device_index)["defaultSampleRate"])


    #Define the "stop" method by handling the audio stream library properly
    def stop(self):
        """
        Stops the audio stream.
        """
        self.__stopped = True
        if self.__audio_stream is not None:
            self.__audio_stream.stop_stream()
            self.__audio_stream.close()


    #Define the "stream" method for our InputStream class.
    #This is where the actual audio stream processing takes place
    def stream(self):
        """
        Starts the audio stream.
        """
        self.__audio_stream = self.__pyaudio.open(
                                     format=self.__format,
                                     channels=self.__channels,
                                     rate=self.__rate,
                                     input=True,
                                     output=False,
                                     frames_per_buffer=self.__chunk_size,
                                     input_device_index=self.__input_device_index)
        self.__stopped = False

        #Run a loop whenever our InputStream is not "stopped"
        #Fetch the audio samples coming from the audio stream object
        #Evaluate the audio signal and ignore it if the signal is below the threshold
        #If it passes the threshold, send out the audio data so it will enter the Darcy AI pipeline
        while not self.__stopped:
            frames = []
            for i in range(0, int(self.__rate / self.__chunk_size * self.__sample_len_sec)):
                data = self.__audio_stream.read(self.__chunk_size, exception_on_overflow=False)
                frames.append(data)

            data = b"".join(frames)
            avg = math.sqrt(abs(audioop.avg(data, 4)))
            if avg < self.__threshold:
                yield StreamData(data, timestamp())
            else:
                print("Silence detected")

    #Define a method for getting the sample rate
    def get_sample_rate(self):
        """
        Returns the sample rate of the audio stream.

        # Returns
        The sample rate of the audio stream.
        """
        return self.__rate
