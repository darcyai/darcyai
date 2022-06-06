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

import pytest
from unittest.mock import patch

from darcyai.output.rest_api_stream import RestApiStream


class TestRestApiStream:
    """
    RestApiStream tests.
    """
    def test_constructor(self):
        stream = RestApiStream("http://localhost")

        assert stream is not None

    def test_constructor_url_is_none(self):
        with pytest.raises(Exception) as context:
            RestApiStream(None)

        assert "url is required" in str(context.value)

    def test_constructor_url_is_not_string(self):
        with pytest.raises(Exception) as context:
            RestApiStream(123)

        assert "url must be a string" in str(context.value)

    def test_constructor_method_is_not_string(self):
        with pytest.raises(Exception) as context:
            RestApiStream("http://localhost", 123)

        assert "method must be a string" in str(context.value)

    def test_constructor_method_is_not_supported(self):
        with pytest.raises(Exception) as context:
            RestApiStream("http://localhost", "GET")

        assert "method must be one of 'POST', 'PUT', or 'PATCH'" in str(
            context.value)

    def test_constructor_content_type_is_not_string(self):
        with pytest.raises(Exception) as context:
            RestApiStream("http://localhost", content_type=123)

        assert "content_type must be a string" in str(context.value)

    def test_constructor_content_type_is_not_supported(self):
        with pytest.raises(Exception) as context:
            RestApiStream("http://localhost", content_type="invalid")

        assert "content_type must be one of 'json' or 'form'" in str(
            context.value)

    def test_constructor_headers_is_not_dict(self):
        with pytest.raises(Exception) as context:
            RestApiStream("http://localhost", headers=123)

        assert "headers must be a dictionary" in str(context.value)

    def test_write_makes_request_with_correct_args(self):
        stream = RestApiStream(
            "http://localhost",
            headers={
                "X-Custom-Header": "value"})

        with patch("requests.request") as mock_request:
            stream.write({"key": "value"})

        mock_request.assert_called_once_with(
            "POST",
            "http://localhost",
            headers={
                "X-Custom-Header": "value",
                "Content-Type": "application/json"},
            json='{"key": "value"}')
