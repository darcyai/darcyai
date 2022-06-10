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

import os
import pathlib
import time

from darcyai.output.csv_output_stream import CSVOutputStream
from darcyai.pipeline import Pipeline
from .sample_input_stream import SampleInputStream
from .sample_perceptor import SamplePerceptor


class Test():
    def __init__(self):
        ping = SampleInputStream(max_runs=1)

        script_dir = pathlib.Path(__file__).parent.absolute()
        self.__csv_file = os.path.join(script_dir, f"{int(time.time())}.csv")
        output_stream = CSVOutputStream(file_path=self.__csv_file)

        self.__pipeline = Pipeline(input_stream=ping,
                                   input_stream_error_handler_callback=self.__input_stream_error_handler_callback)

        self.__pipeline.add_output_stream("output", self.__output_stream_callback, output_stream)

        perceptor = SamplePerceptor(sleep=0.5)
        self.__pipeline.add_perceptor("perceptor", perceptor, input_callback=self.__perceptor_input_callback)

    def act(self):
        self.__pipeline.run()

    def verify(self):
        with open(self.__csv_file) as f:
            data = f.readlines()
            assert len(data) == 1
            assert data[0] == "111,1\n"

    def cleanup(self):
        if os.path.exists(self.__csv_file):
            os.remove(self.__csv_file)

    def __perceptor_input_callback(self, input_data, pom, config):
        return input_data

    def __output_stream_callback(self, pom, input_data):
        return [111, pom.perceptor.data]

    def __input_stream_error_handler_callback(self, exception):
        pass
