import pytest
import time
from collections.abc import Iterable
from unittest.mock import MagicMock

from darcyai.input.input_multi_stream import InputMultiStream
from darcyai.input.input_stream import InputStream
from darcyai.stream_data import StreamData
from input_stream_mock import InputStreamMock


class TestInputMultiStream:
    """
    InputMultiStream tests.
    """
    def test_init_happy_path(self):
        input_multi_stream = InputMultiStream(
            aggregator=lambda x: x, callback=lambda x: x)
        assert input_multi_stream is not None

    def test_init_fails_when_no_callback(self):
        with pytest.raises(Exception):
            InputMultiStream(aggregator=lambda x: x, callback=None)

    def test_init_fails_when_no_aggregator(self):
        with pytest.raises(Exception):
            InputMultiStream(aggregator=None, callback=lambda x: x)

    def test_add_stream_adds_stream_to_input_streams(self):
        input_multi_stream = InputMultiStream(
            aggregator=lambda x: x, callback=lambda x: x)
        input_multi_stream.add_stream("test", InputStream())

        assert input_multi_stream.get_stream("test") is not None

    def test_add_stream_fails_when_stream_with_name_already_exists(self):
        input_multi_stream = InputMultiStream(
            aggregator=lambda x: x, callback=lambda x: x)
        input_multi_stream.add_stream("test", InputStream())

        with pytest.raises(Exception):
            input_multi_stream.add_stream("test", InputStream())

    def test_add_stream_fails_when_stream_is_not_InputStream(self):
        input_multi_stream = InputMultiStream(
            aggregator=lambda x: x, callback=lambda x: x)

        with pytest.raises(Exception) as context:
            input_multi_stream.add_stream("test", True)

        assert "stream is not of type InputStream" in str(context.value)

    def test_get_stream_returns_none(self):
        input_multi_stream = InputMultiStream(
            aggregator=lambda x: x, callback=lambda x: x)
        assert input_multi_stream.get_stream("test") is None

    def test_get_stream_returns_the_stream(self):
        input_stream = InputStream()
        input_multi_stream = InputMultiStream(
            aggregator=lambda x: x, callback=lambda x: x)
        input_multi_stream.add_stream("test", input_stream)

        assert input_multi_stream.get_stream("test") is input_stream

    def test_remove_stream_removes_from_list(self):
        input_multi_stream = InputMultiStream(
            aggregator=lambda x: x, callback=lambda x: x)
        input_multi_stream.add_stream("test", InputStreamMock(range(10)))
        input_multi_stream.remove_stream("test")

        assert input_multi_stream.get_stream("test") is None

    def test_remove_stream_stops_the_stream(self):
        callback_mock = MagicMock()
        input_stream_mock = InputStreamMock(range(10), callback_mock)
        input_multi_stream = InputMultiStream(
            aggregator=lambda x: x, callback=lambda x: x)
        input_multi_stream.add_stream("test", input_stream_mock)

        input_multi_stream.remove_stream("test")

        assert callback_mock.stop.called

    def test_stream_returns_iterator(self):
        callback_mock = MagicMock()
        input_stream_mock = InputStreamMock(range(5), callback_mock)
        input_multi_stream = InputMultiStream(
            aggregator=lambda x: x, callback=lambda x: x)
        input_multi_stream.add_stream("test", input_stream_mock)

        stream = input_multi_stream.stream()

        assert isinstance(stream, Iterable)

    def test_stream_starts_the_input_stream(self):
        callback_mock = MagicMock()
        input_stream_mock = InputStreamMock(range(5), callback_mock)
        input_multi_stream = InputMultiStream(
            aggregator=lambda: StreamData(
                1, 1), callback=lambda x, y: x)
        input_multi_stream.add_stream("test", input_stream_mock)

        for _ in input_multi_stream.stream():
            input_multi_stream.stop()

        assert callback_mock.stream.call_count == 1

    def test_stream_calls_callback(self):
        callback_mock = MagicMock()
        input_stream_mock = InputStreamMock(range(5), MagicMock())
        input_multi_stream = InputMultiStream(
            aggregator=lambda: StreamData(
                1, 1), callback=callback_mock)
        input_multi_stream.add_stream("test", input_stream_mock)

        for _ in input_multi_stream.stream():
            time.sleep(1)
            input_multi_stream.stop()

        assert callback_mock.call_count == 5

    def test_stream_calls_aggregator(self):
        aggregator_mock = MagicMock()
        input_stream_mock = InputStreamMock(range(5), MagicMock())
        input_multi_stream = InputMultiStream(
            aggregator=aggregator_mock, callback=lambda x, y: x)
        input_multi_stream.add_stream("test", input_stream_mock)

        for _ in input_multi_stream.stream():
            input_multi_stream.stop()

        assert aggregator_mock.call_count == 1

    def test_stop_stops_input_stream(self):
        callback_mock = MagicMock()
        input_stream_mock = InputStreamMock(range(10), callback_mock)
        input_multi_stream = InputMultiStream(
            aggregator=lambda x: x, callback=lambda x: x)
        input_multi_stream.add_stream("test", input_stream_mock)

        input_multi_stream.stop()

        assert callback_mock.stop.called
