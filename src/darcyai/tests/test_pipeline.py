import pytest
from unittest.mock import Mock, MagicMock
from darcyai.input.input_stream import InputStream
from darcyai.perception_object_model import PerceptionObjectModel
from darcyai.pipeline import Pipeline
from darcyai.output.output_stream import OutputStream
from darcyai.stream_data import StreamData
from darcyai.tests.input.input_stream_mock import InputStreamMock
from darcyai.tests.perceptor_mock import PerceptorMock


class TestPipeline:
    """
    Pipeline tests.
    """
    def test_constructor(self):
        pipeline = Pipeline(InputStream())
        assert pipeline is not None

    def test_constructor_validates_input_stream_not_none(self):
        with pytest.raises(Exception) as context:
            _ = Pipeline(None)

        assert "input_stream is required" in str(context.value)

    def test_constructor_validates_input_stream_type(self):
        with pytest.raises(Exception) as context:
            _ = Pipeline(1)

        assert "input_stream must be an instance of InputStream" in str(
            context.value)

    def test_add_output_stream_validates_name_not_none(self):
        pipeline = Pipeline(InputStream())

        with pytest.raises(Exception) as context:
            pipeline.add_output_stream(None, None, None)

        assert "name is required" in str(context.value)

    def test_add_output_stream_validates_name_type(self):
        pipeline = Pipeline(InputStream())

        with pytest.raises(Exception) as context:
            pipeline.add_output_stream(1, None, None)

        assert "name must be a string" in str(context.value)

    def test_add_output_stream_fails_when_name_is_not_identifier(self):
        pipeline = Pipeline(InputStream())

        with pytest.raises(Exception) as context:
            pipeline.add_output_stream("not-an-identifier", None, None)

        assert "name must be a valid identifier" in str(context.value)

    def test_add_output_stream_fails_when_name_already_exists(self):
        callback_mock = Mock()

        pipeline = Pipeline(InputStream())
        pipeline.add_output_stream("name", callback_mock, OutputStream())

        with pytest.raises(Exception) as context:
            pipeline.add_output_stream("name", callback_mock, OutputStream())

        assert "output stream with name 'name' already exists" in str(
            context.value)

    def test_add_output_stream_validates_callback_not_none(self):
        pipeline = Pipeline(InputStream())

        with pytest.raises(Exception) as context:
            pipeline.add_output_stream("name", None, None)

        assert "callback is required" in str(context.value)

    def test_add_output_stream_validates_callback_type(self):
        pipeline = Pipeline(InputStream())

        with pytest.raises(Exception) as context:
            pipeline.add_output_stream("name", 1, None)

        assert "callback must be a function" in str(context.value)

    def test_add_output_stream_validates_not_none(self):
        callback_mock = Mock()

        pipeline = Pipeline(InputStream())

        with pytest.raises(Exception) as context:
            pipeline.add_output_stream("name", callback_mock, None)

        assert "output_stream is required" in str(context.value)

    def test_add_output_stream_validates_type(self):
        callback_mock = Mock()

        pipeline = Pipeline(InputStream())

        with pytest.raises(Exception) as context:
            pipeline.add_output_stream("name", callback_mock, 1)

        assert "output_stream must be an instance of OutputStream" in str(
            context.value)

    def test_remove_output_stream_validates_name_not_none(self):
        pipeline = Pipeline(InputStream())

        with pytest.raises(Exception) as context:
            pipeline.remove_output_stream(None)

        assert "name is required" in str(context.value)

    def test_remove_output_stream_validates_name_type(self):
        pipeline = Pipeline(InputStream())

        with pytest.raises(Exception) as context:
            pipeline.remove_output_stream(1)

        assert "name must be a string" in str(context.value)

    def test_remove_output_stream_fails_when_name_does_not_exist(self):
        pipeline = Pipeline(InputStream())

        with pytest.raises(Exception) as context:
            pipeline.remove_output_stream("name")

        assert "output stream with name 'name' does not exist" in str(
            context.value)

    def test_num_of_edge_tpus_returns_default_value(self):
        pipeline = Pipeline(InputStream())
        assert pipeline.num_of_edge_tpus() == 1

    def test_num_of_edge_tpus_returns_correct_value(self):
        pipeline = Pipeline(InputStream(), num_of_edge_tpus=2)
        assert pipeline.num_of_edge_tpus() == 2

    def test_add_perceptor_validates_name_not_none(self):
        pipeline = Pipeline(InputStream())

        input_callback_mock = Mock()
        perceptor_mock = PerceptorMock(sleep=0)

        with pytest.raises(Exception) as context:
            pipeline.add_perceptor(None, perceptor_mock, input_callback_mock)

        assert "name is required" in str(context.value)

    def test_add_perceptor_validates_name_type(self):
        pipeline = Pipeline(InputStream())

        input_callback_mock = Mock()
        perceptor_mock = PerceptorMock(sleep=0)

        with pytest.raises(Exception) as context:
            pipeline.add_perceptor(1, perceptor_mock, input_callback_mock)

        assert "name must be a string" in str(context.value)

    def test_add_perceptor_stream_fails_when_name_is_not_identifier(self):
        pipeline = Pipeline(InputStream())

        input_callback_mock = Mock()
        perceptor_mock = PerceptorMock(sleep=0)

        with pytest.raises(Exception) as context:
            pipeline.add_perceptor(
                "not-an-identifier",
                perceptor_mock,
                input_callback_mock)

        assert "name must be a valid identifier" in str(context.value)

    def test_add_perceptor_validates_perceptor_not_none(self):
        pipeline = Pipeline(InputStream())

        input_callback_mock = Mock()

        with pytest.raises(Exception) as context:
            pipeline.add_perceptor("name", None, input_callback_mock)

        assert "perceptor is required" in str(context.value)

    def test_add_perceptor_validates_perceptor_type(self):
        pipeline = Pipeline(InputStream())

        input_callback_mock = Mock()

        with pytest.raises(Exception) as context:
            pipeline.add_perceptor("name", 1, input_callback_mock)

        assert "perceptor must be an instance of Perceptor" in str(
            context.value)

    def test_add_perceptor_validates_input_callback_type(self):
        pipeline = Pipeline(InputStream())

        perceptor_mock = PerceptorMock(sleep=0)

        with pytest.raises(Exception) as context:
            pipeline.add_perceptor("name", perceptor_mock, 1)

        assert "input_callback must be a function" in str(context.value)

    def test_add_perceptor_validates_output_callback_type(self):
        pipeline = Pipeline(InputStream())

        perceptor_mock = PerceptorMock(sleep=0)
        input_callback_mock = Mock()

        with pytest.raises(Exception) as context:
            pipeline.add_perceptor(
                "name",
                perceptor_mock,
                input_callback_mock,
                output_callback=1)

        assert "output_callback must be a function" in str(context.value)

    def test_add_perceptor_validates_accelerator_idx_type(self):
        pipeline = Pipeline(InputStream())

        perceptor_mock = PerceptorMock(sleep=0)
        input_callback_mock = Mock()

        with pytest.raises(Exception) as context:
            pipeline.add_perceptor(
                "name",
                perceptor_mock,
                input_callback_mock,
                accelerator_idx="1")

        assert "accelerator_idx must be an integer" in str(context.value)

    def test_add_perceptor_validates_accelerator_idx_range(self):
        pipeline = Pipeline(InputStream(), num_of_edge_tpus=2)

        perceptor_mock = PerceptorMock(sleep=0)
        input_callback_mock = Mock()

        with pytest.raises(Exception) as context:
            pipeline.add_perceptor(
                "name",
                perceptor_mock,
                input_callback_mock,
                accelerator_idx=2)

        assert "accelerator_idx must be >= 0 and < 2" in str(context.value)

    def test_add_perceptor_validates_default_config_type(self):
        pipeline = Pipeline(InputStream())

        perceptor_mock = PerceptorMock(sleep=0)
        input_callback_mock = Mock()

        with pytest.raises(Exception) as context:
            pipeline.add_perceptor(
                "name",
                perceptor_mock,
                input_callback_mock,
                default_config=1)

        assert "default_config must be a dictionary" in str(context.value)

    def test_add_perceptor_throws_if_parent_is_not_none_and_does_not_exist(
            self):
        pipeline = Pipeline(InputStream())

        perceptor_mock = PerceptorMock(sleep=0)
        input_callback_mock = Mock()

        with pytest.raises(Exception) as context:
            pipeline.add_perceptor(
                "name",
                perceptor_mock,
                input_callback_mock,
                parent="parent")

        assert "perceptor with name 'parent' does not exist" in str(
            context.value)

    def test_stop_stops_input_stream(self):
        stop_callback_mock = MagicMock()
        input_stream_mock = InputStreamMock(range(10), stop_callback_mock)

        pipeline = Pipeline(input_stream_mock)

        pipeline.stop()

        assert stop_callback_mock.stop.called

    def test_run_starts_input_stream(self):
        callback_mock = MagicMock()
        input_stream_mock = InputStreamMock(range(2), callback_mock)

        pipeline = Pipeline(input_stream_mock)

        pipeline.run()

        assert callback_mock.stream.call_count == 2

    def test_get_pom_returns_pom_with_correct_type(self):
        pipeline = Pipeline(InputStream())

        pom = pipeline.get_pom()

        assert isinstance(pom, PerceptionObjectModel)

    def test_get_current_pulse_number_returns_correct_number(self):
        callback_mock = MagicMock()
        input_stream_mock = InputStreamMock(range(5), callback_mock)

        pipeline = Pipeline(input_stream_mock)

        pipeline.run()

        assert pipeline.get_current_pulse_number() == 5

    def test_get_latest_input_returns_correct_data(self):
        callback_mock = MagicMock()
        input_stream_mock = InputStreamMock(range(5), callback_mock)

        pipeline = Pipeline(input_stream_mock)

        pipeline.run()

        latest_input = pipeline.get_latest_input()

        assert isinstance(latest_input, StreamData)
        assert latest_input.data == 4

    def test_get_historical_input_returns_correct_data(self):
        callback_mock = MagicMock()
        input_stream_mock = InputStreamMock(range(5), callback_mock)

        pipeline = Pipeline(input_stream_mock)

        pipeline.run()

        historical_input = pipeline.get_historical_input(3)

        assert isinstance(historical_input, StreamData)
        assert historical_input.data == 2

    def test_get_historical_input_returns_none_if_index_is_out_of_bounds(self):
        callback_mock = MagicMock()
        input_stream_mock = InputStreamMock(range(1), callback_mock)

        pipeline = Pipeline(input_stream_mock)

        pipeline.run()

        historical_input = pipeline.get_historical_input(5)
        assert historical_input is None

    def test_get_historical_pom_returns_none_if_index_is_out_of_bounds(self):
        callback_mock = MagicMock()
        input_stream_mock = InputStreamMock(range(1), callback_mock)

        pipeline = Pipeline(input_stream_mock)

        pipeline.run()

        historical_pom = pipeline.get_historical_pom(5)
        assert historical_pom is None

    def test_run_perceptor_calls_perceptor_run_with_correct_args(self):
        pipeline = Pipeline(InputStream())

        callback_mock = MagicMock()
        perceptor_mock = PerceptorMock(
            sleep=0, mock=callback_mock)

        input_data = StreamData(1, 0)
        pipeline.run_perceptor(perceptor_mock, input_data)

        callback_mock.run.assert_called_once_with(input_data)

    def test_run_perceptor_calls_perceptor_run_for_each_input_data(self):
        pipeline = Pipeline(InputStream())

        callback_mock = MagicMock()
        perceptor_mock = PerceptorMock(
            sleep=0, mock=callback_mock)

        input_data = [StreamData(1, 1111), StreamData(2, 2222)]
        pipeline.run_perceptor(perceptor_mock, input_data, multi=True)

        assert callback_mock.run.call_count == 2
