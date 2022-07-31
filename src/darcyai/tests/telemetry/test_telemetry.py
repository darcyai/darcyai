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


class TestTelemetry:
    """
    Telemetry tests.
    """
    def test_init_happy_path(self):
        telemetry = Telemetry(darcyai_engine_version="1.0.0", disable_telemetry=False)
        assert telemetry is not None
        assert telemetry.is_enabled() is True

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
