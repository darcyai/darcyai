from unittest.mock import Mock

from darcyai.event_emitter import EventEmitter


class TestEventEmitter:
    """
    EventEmitter tests.
    """
    def test_constructor(self):
        emitter = EventEmitter()
        assert emitter is not None

    def test_on_adds_listener(self):
        emitter = EventEmitter()
        emitter.event_names = ["event_1"]
        emitter.on("event_1", lambda: None)
        assert len(emitter.event_handlers["event_1"]) == 1

    def test_on_adds_multiple_listeners(self):
        emitter = EventEmitter()
        emitter.event_names = ["event_1"]
        emitter.on("event_1", lambda: None)
        emitter.on("event_1", lambda: None)
        assert len(emitter.event_handlers["event_1"]) == 2

    def test_off_removes_listeners(self):
        emitter = EventEmitter()
        emitter.event_names = ["event_1"]
        emitter.on("event_1", lambda: None)
        emitter.on("event_1", lambda: None)
        emitter.off("event_1")
        assert "event_1" not in emitter.event_handlers

    def test_get_event_names(self):
        emitter = EventEmitter()
        event_names = ["event_1", "event_2"]
        emitter.event_names = event_names
        assert emitter.get_event_names() == event_names

    def test_emit_calls_the_listener(self):
        callback_mock = Mock()
        emitter = EventEmitter()
        emitter.event_names = ["event_1"]
        emitter.on("event_1", callback_mock)

        emitter.emit("event_1", "arg1", "arg2")
        callback_mock.assert_called_once_with("arg1", "arg2")

    def test_emit_calls_all_the_listener(self):
        callback_mock1 = Mock()
        callback_mock2 = Mock()
        emitter = EventEmitter()
        emitter.event_names = ["event_1"]
        emitter.on("event_1", callback_mock1)
        emitter.on("event_1", callback_mock2)

        emitter.emit("event_1", "arg1", "arg2")
        callback_mock1.assert_called_once_with("arg1", "arg2")
        callback_mock2.assert_called_once_with("arg1", "arg2")
