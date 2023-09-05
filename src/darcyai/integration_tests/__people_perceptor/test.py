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

from darcyai.input.video_file_stream import VideoFileStream
from darcyai.perceptor.people_perceptor import PeoplePerceptor
from darcyai.pipeline import Pipeline

class Test():
    def __init__(self):
        script_dir = pathlib.Path(__file__).parent.absolute()
        video_file = os.path.join(script_dir, "video.mp4")
        video_stream = VideoFileStream(video_file, process_all_frames=True, loop=False)

        people_ai = PeoplePerceptor()
        people_ai.on("new_person_entered_scene", self.__new_person_callback)

        self.__pipeline = Pipeline(input_stream=video_stream)
        self.__pipeline.add_perceptor("peeps",
                                      people_ai,
                                      input_callback=self.__people_input_callback)

        self.__peeps = 0


    def act(self):
        self.__pipeline.run()


    def verify(self):
        assert self.__peeps == 1


    def cleanup(self):
        pass


    def __people_input_callback(self, input_data, pom, config):
        frame = input_data.data.copy()
        return frame


    def __new_person_callback(self, person_id):
        self.__peeps += 1
