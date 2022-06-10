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

import numpy as np
import pytest
from collections.abc import Iterable
from unittest.mock import patch, MagicMock

from darcyai.input.camera_stream import CameraStream
from darcyai.stream_data import StreamData


class TestCameraStream:
    """
    CameraStream tests.
    """

    def test_init(self):
        camera_stream = CameraStream(video_device="/dev/video0")
        assert camera_stream is not None

    @patch("darcyai.imutils.video.VideoStream")
    def test_start_returns_iterator(self, imutils_mock):
        read_mock = MagicMock()
        read_mock.read.return_value = np.random.randint(
            0, 255, size=(640, 480, 3), dtype=np.uint8)

        start_mock = MagicMock()
        start_mock.start.return_value = read_mock

        imutils_mock.return_value = start_mock

        camera_stream = CameraStream(video_device="/dev/video0", use_pi_camera=True)
        stream = camera_stream.stream()

        assert isinstance(stream, Iterable)

    @patch("darcyai.imutils.video.VideoStream")
    def test_stream_returns_StreamData(self, imutils_mock):
        read_mock = MagicMock()
        read_mock.read.return_value = np.random.randint(
            0, 255, size=(640, 480, 3), dtype=np.uint8)

        start_mock = MagicMock()
        start_mock.start.return_value = read_mock

        imutils_mock.return_value = start_mock

        camera_stream = CameraStream(video_device="/dev/video0", use_pi_camera=True)
        stream = camera_stream.stream()

        frame = next(stream)
        assert isinstance(frame, StreamData)

    @patch("darcyai.imutils.video.VideoStream")
    def test_stream_runs_until_stopped(self, imutils_mock):
        read_mock = MagicMock()
        read_mock.read.return_value = np.random.randint(
            0, 255, size=(640, 480, 3), dtype=np.uint8)

        start_mock = MagicMock()
        start_mock.start.return_value = read_mock

        imutils_mock.return_value = start_mock

        camera_stream = CameraStream(video_device="/dev/video0", use_pi_camera=True)
        stream = camera_stream.stream()

        count = 0
        for _ in stream:
            count += 1
            if count == 5:
                camera_stream.stop()

            if count > 5:
                pytest.fail("Stream should have stopped after 5 iterations")

    @patch("darcyai.imutils.video.VideoStream")
    def test_stream_flips_frame(self, imutils_mock):
        read_mock = MagicMock()
        read_mock.read.return_value = np.array(
            [[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [0, 1, 2]]])

        start_mock = MagicMock()
        start_mock.start.return_value = read_mock

        imutils_mock.return_value = start_mock

        camera_stream = CameraStream(
            flip_frames=True, video_device="/dev/video0", use_pi_camera=True)
        stream = camera_stream.stream()

        frame = next(stream)
        assert np.array_equal(frame.data, np.array(
            [[[4, 5, 6], [1, 2, 3]], [[0, 1, 2], [7, 8, 9]]]))

    @patch("darcyai.imutils.video.VideoStream")
    def test_stream_fails_if_video_stream_cannot_be_started(
            self, imutils_mock):
        read_mock = MagicMock()
        read_mock.read.return_value = None

        start_mock = MagicMock()
        start_mock.start.return_value = read_mock

        imutils_mock.return_value = start_mock

        camera_stream = CameraStream(video_device="/dev/video0", use_pi_camera=True)
        stream = camera_stream.stream()

        with pytest.raises(Exception) as context:
            _ = next(stream)

        assert "Could not initialize video stream" in str(context.value)
