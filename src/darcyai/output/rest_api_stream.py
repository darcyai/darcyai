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
import requests
from requests.models import Response
from typing import Dict, Any

from darcyai.output.output_stream import OutputStream
from darcyai.utils import validate_not_none, validate_type, validate


class RestApiStream(OutputStream):
    """
    A stream that sends data to a REST API.

    # Arguments
    url (str): The URL of the REST API.
    method (str): The HTTP method to use.
        Must be one of 'POST', 'PUT', 'PATCH'.
        Defaults to `POST`.
    content_type (str): The content type of the data.
        Must be one of 'json' or 'form'.
        Defaults to `json`.
    headers (dict): The headers to send with the request. Defaults to `None`.

    # Examples
    ```python
    >>> from darcyai.output.rest_api_stream import RestApiStream
    >>> rest_api_stream = RestApiStream(url="http://localhost:5000/api/v1/data",
                                        method="POST",
                                        content_type="json")
                                        headers={"Authorization": "Bearer ..."})
    ```
    """

    def __init__(self,
                 url: str,
                 method: str = "POST",
                 content_type: str = "json",
                 headers: Dict[str, str] = None) -> None:
        super().__init__()

        validate_not_none(url, "url is required")
        validate_type(url, str, "url must be a string")
        self.__url = url

        validate_not_none(method, "method is required")
        validate_type(method, str, "method must be a string")
        validate(method in ["POST", "PUT", "PATCH"],
                 "method must be one of 'POST', 'PUT', or 'PATCH'")
        self.__method = method

        validate_not_none(content_type, "content_type is required")
        validate_type(content_type, str, "content_type must be a string")
        validate(
            content_type in [
                "json",
                "form"],
            "content_type must be one of 'json' or 'form'")
        self.__content_type = content_type

        if headers is not None:
            validate_type(headers, dict, "headers must be a dictionary")
            self.__headers = headers
        else:
            self.__headers = {}

        if content_type == "json":
            self.__headers["Content-Type"] = "application/json"
        elif content_type == "form":
            self.__headers["Content-Type"] = "application/x-www-form-urlencoded"

        self.set_config_schema([])

    def write(self, data: Any) -> Response:
        """
        Processes the data and writes it to the output stream.

        # Arguments
        data (Any): The data to be written to the output stream.

        # Returns
        Response: The response from the REST API.

        # Examples
        ```python
        >>> from darcyai.output.rest_api_stream import RestApiStream
        >>> rest_api_stream = RestApiStream(url="http://localhost:5000/api/v1/data",
                                            method="POST",
                                            content_type="json")
                                            headers={"Authorization": "Bearer ..."})
        >>> response = rest_api_stream.write({"data": "some data"})
        ```
        """
        if data is None and self.ignore_none:
            return

        if self.__content_type == "json":
            return requests.request(
                self.__method,
                self.__url,
                json=json.dumps(data),
                headers=self.__headers)
        else:
            return requests.request(
                self.__method,
                self.__url,
                data=data,
                headers=self.__headers)

    def close(self) -> None:
        """
        Closes the output stream.
        """
        pass
