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
import os
from unittest import mock

from darcyai.telemetry.telemetry import Telemetry
from darcyai.tests.perceptor_mock import PerceptorMock
from sample_input_stream import SampleInputStream
from sample_output_stream import SampleOutputStream


class TestTelemetry:
    """
    Telemetry tests.
    """
    def test_init_happy_path(self):
        telemetry = Telemetry(darcyai_engine_version="1.0.0", disable_telemetry=False)
        assert telemetry is not None
        assert telemetry.is_enabled() is True
        assert telemetry._Telemetry__telemetry.send is False

    def test_init_disable_telemetry(self):
        telemetry = Telemetry(darcyai_engine_version="1.0.0", disable_telemetry=True)
        assert telemetry is not None
        assert telemetry.is_enabled() is False

    @mock.patch.dict(os.environ, {"DARCYAI_DISABLE_TELEMETRY": "False"})
    def test_init_disable_telemetry_env_False(self):
        telemetry = Telemetry(darcyai_engine_version="1.0.0", disable_telemetry=False)
        assert telemetry is not None
        assert telemetry.is_enabled() is True

    @mock.patch.dict(os.environ, {"DARCYAI_DISABLE_TELEMETRY": "false"})
    def test_init_disable_telemetry_env_false(self):
        telemetry = Telemetry(darcyai_engine_version="1.0.0", disable_telemetry=False)
        assert telemetry is not None
        assert telemetry.is_enabled() is True

    @mock.patch.dict(os.environ, {"DARCYAI_DISABLE_TELEMETRY": "0"})
    def test_init_disable_telemetry_env_0(self):
        telemetry = Telemetry(darcyai_engine_version="1.0.0", disable_telemetry=False)
        assert telemetry is not None
        assert telemetry.is_enabled() is True

    @mock.patch.dict(os.environ, {"DARCYAI_DISABLE_TELEMETRY": ""})
    def test_init_disable_telemetry_env_empty(self):
        telemetry = Telemetry(darcyai_engine_version="1.0.0", disable_telemetry=False)
        assert telemetry is not None
        assert telemetry.is_enabled() is True

    @mock.patch.dict(os.environ, {"DARCYAI_DISABLE_TELEMETRY": "1"})
    def test_init_disable_telemetry_env_1(self):
        telemetry = Telemetry(darcyai_engine_version="1.0.0", disable_telemetry=False)
        assert telemetry is not None
        assert telemetry.is_enabled() is False

    @mock.patch.dict(os.environ, {"DARCYAI_DISABLE_TELEMETRY": "True"})
    def test_init_disable_telemetry_env_1(self):
        telemetry = Telemetry(darcyai_engine_version="1.0.0", disable_telemetry=False)
        assert telemetry is not None
        assert telemetry.is_enabled() is False

    def test_get_type_name(self):
        telemetry = Telemetry(darcyai_engine_version="1.0.0", disable_telemetry=False)
        assert telemetry.get_type_name(telemetry) == "darcyai.telemetry.telemetry.Telemetry"

    def test_hash_pipeline_config(self):
        telemetry = Telemetry(darcyai_engine_version="1.0.0", disable_telemetry=False)
        hash_1 = telemetry.hash_pipeline_config(SampleInputStream(), {"a": PerceptorMock(), "b": PerceptorMock() }, [{"a"}, {"b"}], {"o": { "stream": SampleOutputStream() }})
        hash_2 = telemetry.hash_pipeline_config(SampleInputStream(), {"a": PerceptorMock(), "b": PerceptorMock() }, [{"a"}, {"b"}], {"o": { "stream": SampleOutputStream() }})
        hash_3 = telemetry.hash_pipeline_config(SampleInputStream(), {"a": PerceptorMock(), "b": PerceptorMock(), "c": PerceptorMock() }, [{"a"}, {"b", "c"}], {"o": { "stream": SampleOutputStream() }})
        hash_4 = telemetry.hash_pipeline_config(SampleInputStream(), {"a": PerceptorMock(), "b": PerceptorMock(), "c": Telemetry("1.0.0") }, [{"c"}, {"a", "b"}], {"o": { "stream": SampleOutputStream() }})

        assert hash_1 == hash_2
        assert hash_1 != hash_3
        assert hash_3 != hash_4