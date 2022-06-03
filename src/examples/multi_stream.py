# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

from darcyai.input.camera_stream import CameraStream
from darcyai.input.input_multi_stream import InputMultiStream
from darcyai.tests.perceptor_mock import PerceptorMock
from darcyai.pipeline import Pipeline
from darcyai.stream_data import StreamData
from sample_input_stream import SampleInputStream
from sample_output_stream import SampleOutputStream


class MultiStreamDemo():
    def __init__(self):
        self.__last_frame = None
        self.__last_frame_timestamp = 0
        self.__send = False

        camera = CameraStream(video_device="/dev/video0")
        ping = SampleInputStream()

        input_stream = InputMultiStream(callback=self.__input_stream_callback, aggregator=self.__input_aggregator)
        input_stream.add_stream("camera", camera)
        input_stream.add_stream("ping", ping)

        output_stream = SampleOutputStream()

        self.__pipeline = Pipeline(input_stream=input_stream)

        self.__pipeline.add_output_stream("output", self.__output_stream_callback, output_stream)

        p1 = PerceptorMock()
        self.__pipeline.add_perceptor("p1", p1, accelerator_idx=0, input_callback=self.__perceptor_input_callback)


    def run(self):
        self.__pipeline.run()


    def __input_stream_callback(self, stream_name, stream_data):
        if stream_name == "camera":
            self.__last_frame = stream_data.data
            self.__last_frame_timestamp = stream_data.timestamp
        elif stream_name == "ping":
            self.__send = True


    def __input_aggregator(self):
        while not self.__send:
            continue

        self.__send = False
        
        return StreamData({ "camera": self.__last_frame }, self.__last_frame_timestamp)


    def __perceptor_input_callback(self, input_data, pom, config):
        return input_data


    def __output_stream_callback(self, pom, input_data):
        pass


if __name__ == "__main__":
    demo = MultiStreamDemo()
    demo.run()