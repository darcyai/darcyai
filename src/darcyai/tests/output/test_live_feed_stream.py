import pytest
from flask import Flask

from darcyai.output.live_feed_stream import LiveFeedStream


class TestLiveFeedStream:
    """
    LiveFeedStream tests.
    """
    def test_constructor_validates_flask_app_type(self):
        with pytest.raises(Exception) as context:
            LiveFeedStream(path="/", flask_app=1)

        assert "flask_app must be of type Flask" in str(context.value)

    def test_constructor_fails_when_port_is_not_provided(self):
        with pytest.raises(Exception) as context:
            LiveFeedStream(path="/")

        assert "port is required" in str(context.value)

    def test_constructor_validates_port_type(self):
        with pytest.raises(Exception) as context:
            LiveFeedStream(path="/", port="1")

        assert "port must be of type int" in str(context.value)

    def test_constructor_validates_port_range(self):
        with pytest.raises(Exception) as context:
            LiveFeedStream(path="/", port=70000)

        assert "port must be between 0 and 65535" in str(context.value)

    def test_constructor_fails_when_host_is_not_provided(self):
        with pytest.raises(Exception) as context:
            LiveFeedStream(path="/", port=1)

        assert "host is required" in str(context.value)

    def test_constructor_validates_host_type(self):
        with pytest.raises(Exception) as context:
            LiveFeedStream(path="/", port=1, host=1)

        assert "host must be a string" in str(context.value)

    def test_constructor_fails_when_path_is_not_provided(self):
        with pytest.raises(Exception) as context:
            LiveFeedStream(path=None, port=1, host="localhost")

        assert "path is required" in str(context.value)

    def test_constructor_validates_path_type(self):
        with pytest.raises(Exception) as context:
            LiveFeedStream(port=1, host="localhost", path=1)

        assert "path must be a string" in str(context.value)

    def test_constructor_fails_when_fps_is_none(self):
        with pytest.raises(Exception) as context:
            LiveFeedStream(port=1, host="localhost", path="/", fps=None)

        assert "fps must be a positive integer" in str(context.value)

    def test_constructor_validates_fps_type(self):
        with pytest.raises(Exception) as context:
            LiveFeedStream(port=1, host="localhost", path="/", fps="1")

        assert "fps must be a positive integer" in str(context.value)

    def test_constructor_validates_fps_range(self):
        with pytest.raises(Exception) as context:
            LiveFeedStream(port=1, host="localhost", path="/", fps=0)

        assert "fps must be greater than 0" in str(context.value)

    def test_constructor_fails_when_quality_is_none(self):
        with pytest.raises(Exception) as context:
            LiveFeedStream(port=1, host="localhost", path="/", quality=None)

        assert "quality must be a positive integer" in str(context.value)

    def test_constructor_validates_quality_type(self):
        with pytest.raises(Exception) as context:
            LiveFeedStream(port=1, host="localhost", path="/", quality="1")

        assert "quality must be a positive integer" in str(context.value)

    def test_constructor_validates_quality_range(self):
        with pytest.raises(Exception) as context:
            LiveFeedStream(port=1, host="localhost", path="/", quality=101)

        assert "quality must be between 0 and 100" in str(context.value)

    def test_set_fps_validates_fps_type(self):
        flask_app = Flask(__name__)
        stream = LiveFeedStream(
            port=1,
            host="localhost",
            path="/",
            flask_app=flask_app)
        with pytest.raises(Exception) as context:
            stream.set_fps(fps="1")

        assert "fps must be a positive integer" in str(context.value)

    def test_set_fps_validates_fps_range(self):
        flask_app = Flask(__name__)
        stream = LiveFeedStream(
            port=1,
            host="localhost",
            path="/",
            flask_app=flask_app)
        with pytest.raises(Exception) as context:
            stream.set_fps(fps=0)

        assert "fps must be greater than 0" in str(context.value)

    def test_set_fps_fails_when_fps_is_none(self):
        flask_app = Flask(__name__)
        stream = LiveFeedStream(
            port=1,
            host="localhost",
            path="/",
            flask_app=flask_app)
        with pytest.raises(Exception) as context:
            stream.set_fps(fps=None)

        assert "fps must be a positive integer" in str(context.value)

    def test_get_fps_returns_current_fps(self):
        flask_app = Flask(__name__)
        stream = LiveFeedStream(
            port=1,
            host="localhost",
            path="/",
            flask_app=flask_app,
            fps=10)
        assert stream.get_fps() == 10

    def test_set_quality_validates_quality_type(self):
        flask_app = Flask(__name__)
        stream = LiveFeedStream(
            port=1,
            host="localhost",
            path="/",
            flask_app=flask_app)
        with pytest.raises(Exception) as context:
            stream.set_quality(quality="1")

        assert "quality must be a positive integer" in str(context.value)

    def test_set_quality_validates_quality_range(self):
        flask_app = Flask(__name__)
        stream = LiveFeedStream(
            port=1,
            host="localhost",
            path="/",
            flask_app=flask_app)
        with pytest.raises(Exception) as context:
            stream.set_quality(quality=101)

        assert "quality must be between 0 and 100" in str(context.value)

    def test_set_quality_fails_when_quality_is_none(self):
        flask_app = Flask(__name__)
        stream = LiveFeedStream(
            port=1,
            host="localhost",
            path="/",
            flask_app=flask_app)
        with pytest.raises(Exception) as context:
            stream.set_quality(quality=None)

        assert "quality must be a positive integer" in str(context.value)

    def test_get_quality_returns_current_quality(self):
        flask_app = Flask(__name__)
        stream = LiveFeedStream(
            port=1,
            host="localhost",
            path="/",
            flask_app=flask_app,
            quality=10)
        assert stream.get_quality() == 10
