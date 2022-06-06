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

from typing import Any

from darcyai.serializable import Serializable


class StreamData(Serializable):
    """
    Class to hold data from a stream.

    # Arguments
    data (Any): The data to be stored.
    timestamp (int): The timestamp of the data.
    """

    def __init__(self, data: Any, timestamp: int):
        super().__init__()
        self.data = data
        self.timestamp = timestamp

    def serialize(self) -> dict:
        """
        Serializes the data.

        # Returns
        dict: The serialized data.
        """
        return {
            "data": self.data,
            "timestamp": self.timestamp
        }
