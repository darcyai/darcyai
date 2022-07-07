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

import cv2
import os
import pathlib

class Test():
    __SNIPPETS = [
        "1_imports.py",
        "test_2_1_initialize_input.py",
        "2_2_initialize_pipeline_output.py",
        "3_output_callback.py",
        "4_init_perceptor.py",
        "5_add_perceptor.py",
        "6_configure.py",
        "7_start.py",
        "test_8_stop.py",
    ]

    def __init__(self):
        script_dir = pathlib.Path(__file__).parent.absolute()

        demo = ""
        for snippet in self.__SNIPPETS:
            snippet_file = os.path.join(script_dir, "..", "..", "..", "..", ".assets", "snippets", snippet)
            with open(snippet_file) as f:
                demo += f.read()
                demo += "\n\n"

        # save demo file
        self.__demo_file = os.path.join(script_dir, "demo.py")
        with open(self.__demo_file, "w") as f:
            f.write(demo)

        self.__result = ""


    def act(self):
        exec(open(self.__demo_file).read())

    def verify(self):
        pass

    def cleanup(self):
        try:
            if os.path.exists(self.__demo_file):
                os.remove(self.__demo_file)
        except Exception:
            pass
