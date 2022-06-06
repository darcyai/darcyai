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

from typing import Iterable

from darcyai.stream_data import StreamData


class InputStream:
    """
    Base class for reading input from a stream.

    # Examples
    ```python
    >>> from darcyai.input.input_stream import InputStream
    >>> from darcyai.stream_data import StreamData

    >>> class MyInputStream(InputStream):
    ...     def stream(self):
    ...         yield StreamData("data", 1234567890)

    >>>     def stop(self):
    ...         pass
    ```
    """
    def __init__(self):
        pass

    def stream(self) -> Iterable[StreamData]:
        """
        Returns a generator that yields a stream of input.

        # Returns
        A generator that yields a stream of input.
        """
        raise NotImplementedError("InputStream.stream() not implemented")

    def stop(self) -> None:
        """
        Stops the stream.
        """
        raise NotImplementedError("InputStream.stop() not implemented")
