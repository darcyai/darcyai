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
from unittest.mock import Mock, patch

from darcyai.perceptor.coral.object_detection_perceptor import ObjectDetectionPerceptor


@pytest.mark.skip(reason="Fix coral dependency")
class TestObjectDetectionPerceptor:
    """
    Tests for the ObjectDetectionPerceptor class.
    """

    def test_init_happy_path(self):
        mock_list_edge_tpus = Mock()
        mock_list_edge_tpus.return_value = ["a_coral"]
        with patch("darcyai.perceptor.coral.edgetpu.list_edge_tpus", mock_list_edge_tpus):
            perceptor = ObjectDetectionPerceptor(threshold=0.5, model_path="model.tflite")

        assert perceptor is not None

    def test_constructor_fails_if_threshold_is_none(self):
        mock_list_edge_tpus = Mock()
        mock_list_edge_tpus.return_value = ["a_coral"]
        with patch("darcyai.perceptor.coral.edgetpu.list_edge_tpus", mock_list_edge_tpus):
            with pytest.raises(Exception) as context:
                ObjectDetectionPerceptor(threshold=None, model_path="model.tflite")

        assert "threshold is required" in str(context.value)

    def test_constructor_fails_if_threshold_is_not_a_number(self):
        mock_list_edge_tpus = Mock()
        mock_list_edge_tpus.return_value = ["a_coral"]
        with patch("darcyai.perceptor.coral.edgetpu.list_edge_tpus", mock_list_edge_tpus):
            with pytest.raises(Exception) as context:
                ObjectDetectionPerceptor(threshold="0.5", model_path="model.tflite")

        assert "threshold must be a number" in str(context.value)

    def test_constructor_fails_if_threshold_is_out_of_range(self):
        mock_list_edge_tpus = Mock()
        mock_list_edge_tpus.return_value = ["a_coral"]
        with patch("darcyai.perceptor.coral.edgetpu.list_edge_tpus", mock_list_edge_tpus):
            with pytest.raises(Exception) as context:
                ObjectDetectionPerceptor(threshold=1.1, model_path="model.tflite")

        assert "threshold must be between 0 and 1" in str(context.value)

    def test_constructor_fails_if_model_path_is_none(self):
        mock_list_edge_tpus = Mock()
        mock_list_edge_tpus.return_value = ["a_coral"]
        with patch("darcyai.perceptor.coral.edgetpu.list_edge_tpus", mock_list_edge_tpus):
            with pytest.raises(Exception) as context:
                ObjectDetectionPerceptor(threshold=0.5, model_path=None)

        assert "model_path is required" in str(context.value)

    def test_constructor_fails_if_labels_file_is_not_string(self):
        mock_list_edge_tpus = Mock()
        mock_list_edge_tpus.return_value = ["a_coral"]
        with patch("darcyai.perceptor.coral.edgetpu.list_edge_tpus", mock_list_edge_tpus):
            with pytest.raises(Exception) as context:
                ObjectDetectionPerceptor(threshold=0.5, model_path="model.tflite", labels_file=1)

        assert "labels_file must be a string" in str(context.value)

    def test_load_fails_when_accelerator_idx_is_not_number(self):
        mock_list_edge_tpus = Mock()
        mock_list_edge_tpus.return_value = ["a_coral"]
        with patch("darcyai.perceptor.coral.edgetpu.list_edge_tpus", mock_list_edge_tpus):
            perceptor = ObjectDetectionPerceptor(threshold=0.5,
                                                 model_path="model.tflite")

        with pytest.raises(Exception) as context:
            perceptor.load(accelerator_idx="1")

        assert "accelerator_idx must be an integer" in str(context.value)

    def test_load_fails_when_accelerator_idx_is_negative(self):
        mock_list_edge_tpus = Mock()
        mock_list_edge_tpus.return_value = ["a_coral"]
        with patch("darcyai.perceptor.coral.edgetpu.list_edge_tpus", mock_list_edge_tpus):
            perceptor = ObjectDetectionPerceptor(threshold=0.5,
                                                 model_path="model.tflite")

        with pytest.raises(Exception) as context:
            perceptor.load(accelerator_idx=-1)

        assert "accelerator_idx must be greater than or equal to 0" in str(context.value)

    def test_load_calls_make_interpreter_with_correct_args_when_accelerator_idx_is_given(self):
        mock_interpreter = Mock()
        mock_interpreter.get_input_details.return_value = [{"shape": [0, 0, 0]}]

        mock_make_interpreter = Mock()
        mock_make_interpreter.return_value = mock_interpreter

        mock_list_edge_tpus = Mock()
        mock_list_edge_tpus.return_value = ["a_coral"]
        with patch("darcyai.perceptor.coral.edgetpu.list_edge_tpus", mock_list_edge_tpus):
            perceptor = ObjectDetectionPerceptor(threshold=0.5,
                                                 model_path="model.tflite")

        with patch("darcyai.perceptor.coral.edgetpu.make_interpreter", mock_make_interpreter):
            perceptor.load(accelerator_idx=1)

        mock_make_interpreter.assert_called_once_with("model.tflite", device=":1")

    def test_load_calls_make_interpreter_with_correct_args_when_accelerator_idx_is_none(self):
        mock_interpreter = Mock()
        mock_interpreter.get_input_details.return_value = [{"shape": [0, 0, 0]}]

        mock_make_interpreter = Mock()
        mock_make_interpreter.return_value = mock_interpreter

        mock_list_edge_tpus = Mock()
        mock_list_edge_tpus.return_value = ["a_coral"]
        with patch("darcyai.perceptor.coral.edgetpu.list_edge_tpus", mock_list_edge_tpus):
            perceptor = ObjectDetectionPerceptor(threshold=0.5,
                                                 model_path="model.tflite")

        with patch("darcyai.perceptor.coral.edgetpu.make_interpreter", mock_make_interpreter):
            perceptor.load(accelerator_idx=None)

        mock_make_interpreter.assert_called_once_with("model.tflite")

    def test_load_parses_labels_when_labels_file_provided(self):
        mock_interpreter = Mock()
        mock_interpreter.get_input_details.return_value = [{"shape": [0, 0, 0]}]

        mock_make_interpreter = Mock()
        mock_make_interpreter.return_value = mock_interpreter

        mock_dataset = Mock()

        mock_list_edge_tpus = Mock()
        mock_list_edge_tpus.return_value = ["a_coral"]
        with patch("darcyai.perceptor.coral.edgetpu.list_edge_tpus", mock_list_edge_tpus):
            with patch("darcyai.perceptor.coral.edgetpu.make_interpreter", mock_make_interpreter):
                with patch("darcyai.perceptor.coral.dataset.read_label_file", mock_dataset):
                    _ = ObjectDetectionPerceptor(threshold=0.5,
                                                 model_path="model.tflite",
                                                 labels_file="labels.txt")

        mock_dataset.assert_called_once_with("labels.txt")
