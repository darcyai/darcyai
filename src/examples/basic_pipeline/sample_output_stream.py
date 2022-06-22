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

# Add the DarcyAI components that we need, particularly the OutputStream
from darcyai.output.output_stream import OutputStream

# Define our own OutputStream class


class SampleOutputStream(OutputStream):
    def __init__(self):
        # Call init on the parent class
        super().__init__()

    # Define our "write" method for the OutputStream class
    def write(self, data):
        pass

    # Define our "close" method for the OutputStream class
    def close(self):
        pass
