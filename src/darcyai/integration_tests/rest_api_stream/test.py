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

import json
import logging
import random
import threading
import time
from flask import Flask, request, Response

from darcyai.output.rest_api_stream import RestApiStream
from darcyai.pipeline import Pipeline
from .sample_input_stream import SampleInputStream
from .sample_perceptor import SamplePerceptor


class Test():
    def __init__(self):
        self.__port_number = random.randint(40000, 49999)

        ping = SampleInputStream(max_runs=1)
        output_stream = RestApiStream(url=f"http://0.0.0.0:{self.__port_number}/post")

        self.__pipeline = Pipeline(input_stream=ping,
                                   input_stream_error_handler_callback=self.__input_stream_error_handler_callback)

        self.__pipeline.add_output_stream("output", self.__output_stream_callback, output_stream)

        perceptor = SamplePerceptor(sleep=0.5)
        self.__pipeline.add_perceptor("perceptor", perceptor, input_callback=self.__perceptor_input_callback)

        self.__perception_results = []

        self.__flask_app = Flask(__name__)
        threading.Thread(target=self.__start_api_server).start()
        time.sleep(2)


    def act(self):
        self.__pipeline.run()


    def verify(self):
        assert len(self.__perception_results) == 1
        assert self.__perception_results[0] == 1


    def cleanup(self):
        pass


    def __perceptor_input_callback(self, input_data, pom, config):
        return input_data


    def __output_stream_callback(self, pom, input_data):
        return { "perception_result": pom.perceptor.data }


    def __input_stream_error_handler_callback(self, exception):
        pass


    def __post(self):
        data = json.loads(request.json)
        self.__perception_results.append(data["perception_result"])
        return Response(status=200)


    def __start_api_server(self) -> None:
        logging.getLogger("requests").setLevel(logging.ERROR)
        logging.getLogger("urllib3").setLevel(logging.ERROR)
        logging.getLogger('werkzeug').setLevel(logging.ERROR)

        self.__flask_app.add_url_rule("/post", "post", self.__post, methods=["POST"])

        ssl_context = None
        self.__flask_app.run(
            host="0.0.0.0",
            port=self.__port_number,
            ssl_context=ssl_context,
            debug=False)
