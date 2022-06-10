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

from darcyai.pipeline import Pipeline

from .sample_input_stream import SampleInputStream
from .sample_output_stream import SampleOutputStream
from .sample_perceptor import SamplePerceptor


class Test():
    def __init__(self):
        ping = SampleInputStream(max_runs=2)
        output_stream = SampleOutputStream()

        self.__pipeline = Pipeline(input_stream=ping,
                                   input_stream_error_handler_callback=self.__input_stream_error_handler_callback)

        self.__pipeline.add_output_stream("output", self.__output_stream_callback, output_stream)

        perceptor = SamplePerceptor(sleep=0.5)
        self.__pipeline.add_perceptor("perceptor", perceptor, input_callback=self.__perceptor_input_callback)

        self.__perception_results = []

    def act(self):
        self.__pipeline.run()

    def verify(self):
        assert len(self.__perception_results) == 2
        assert self.__perception_results[0] == 1
        assert self.__perception_results[1] == 2

    def cleanup(self):
        pass

    def __perceptor_input_callback(self, input_data, pom, config):
        return input_data

    def __output_stream_callback(self, pom, input_data):
        self.__perception_results.append(pom.perceptor.data)

    def __input_stream_error_handler_callback(self, exception):
        pass
