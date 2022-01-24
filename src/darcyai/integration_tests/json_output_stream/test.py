import os
import pathlib
import time

from darcyai.output.json_output_stream import JSONOutputStream
from darcyai.pipeline import Pipeline
from .sample_input_stream import SampleInputStream
from .sample_perceptor import SamplePerceptor


class Test():
    def __init__(self):
        ping = SampleInputStream(max_runs=1)

        script_dir = pathlib.Path(__file__).parent.absolute()
        self.__json_file = os.path.join(script_dir, f"{int(time.time())}.json")
        output_stream = JSONOutputStream(file_path=self.__json_file)

        self.__pipeline = Pipeline(input_stream=ping,
                                   input_stream_error_handler_callback=self.__input_stream_error_handler_callback)

        self.__pipeline.add_output_stream("output", self.__output_stream_callback, output_stream)

        perceptor = SamplePerceptor(sleep=0.5)
        self.__pipeline.add_perceptor("perceptor", perceptor, input_callback=self.__perceptor_input_callback)


    def act(self):
        self.__pipeline.run()


    def verify(self):
        with open(self.__json_file) as f:
            data = f.readlines()
            assert len(data) == 1
            assert data[0] == "{\"perception_result\": 1}"

    def cleanup(self):
        if os.path.exists(self.__json_file):
            os.remove(self.__json_file)


    def __perceptor_input_callback(self, input_data, pom, config):
        return input_data


    def __output_stream_callback(self, pom, input_data):
        return { "perception_result": pom.perceptor.data }


    def __input_stream_error_handler_callback(self, exception):
        pass
