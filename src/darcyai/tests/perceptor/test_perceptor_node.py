# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

import pytest
from unittest.mock import Mock, patch

from darcyai.perceptor.perceptor_node import PerceptorNode
from darcyai.tests.perceptor_mock import PerceptorMock
from darcyai.perception_object_model import PerceptionObjectModel
from darcyai.stream_data import StreamData


class TestPerceptor:
    """
    PerceptorNode tests.
    """
    def test_init_happy_path(self):
        input_callback_mock = Mock()
        perceptor_mock = PerceptorMock(sleep=0)

        perceptor_node = PerceptorNode(
            "name",
            perceptor_mock,
            input_callback_mock.method,
            multi=False,
            accelerator_idx=0)

        assert perceptor_node is not None

    def test_init_fails_when_perceptor_name_is_none(self):
        input_callback_mock = Mock()
        perceptor_mock = PerceptorMock(sleep=0)

        with pytest.raises(Exception) as context:
            PerceptorNode(
                None,
                perceptor_mock,
                input_callback_mock.method,
                multi=False,
                accelerator_idx=0)

        assert "perceptor_name is required" in str(context.value)

    def test_init_fails_when_perceptor_name_is_not_of_type_string(self):
        input_callback_mock = Mock()
        perceptor_mock = PerceptorMock(sleep=0)

        with pytest.raises(Exception) as context:
            PerceptorNode(
                1,
                perceptor_mock,
                input_callback_mock.method,
                multi=False,
                accelerator_idx=0)

        assert "perceptor_name must be a string" in str(context.value)

    def test_init_fails_when_perceptor_is_none(self):
        input_callback_mock = Mock()

        with pytest.raises(Exception) as context:
            PerceptorNode(
                "name",
                None,
                input_callback_mock.method,
                multi=False,
                accelerator_idx=0)

        assert "perceptor is required" in str(context.value)

    def test_init_fails_when_perceptor_is_not_of_type_perceptor(self):
        input_callback_mock = Mock()

        with pytest.raises(Exception) as context:
            PerceptorNode(
                "name",
                1,
                input_callback_mock.method,
                multi=False,
                accelerator_idx=0)

        assert "perceptor must be an instance of Perceptor" in str(
            context.value)

    def test_init_fails_when_input_callback_is_not_of_type_function(self):
        perceptor_mock = PerceptorMock(sleep=0)

        with pytest.raises(Exception) as context:
            PerceptorNode(
                "name",
                perceptor_mock,
                1,
                multi=False,
                accelerator_idx=0)

        assert "input_callback must be a function" in str(context.value)

    def test_init_fails_when_output_callback_is_not_of_type_function(self):
        input_callback_mock = Mock()
        perceptor_mock = PerceptorMock(sleep=0)

        with pytest.raises(Exception) as context:
            PerceptorNode(
                "name",
                perceptor_mock,
                input_callback_mock.method,
                output_callback=1,
                multi=False,
                accelerator_idx=0)

        assert "output_callback must be a function" in str(context.value)

    def test_add_child_perceptor_adds_perceptor_to_children(self):
        input_callback_mock = Mock()
        perceptor_mock = PerceptorMock(sleep=0)
        perceptor_node = PerceptorNode(
            "parent",
            perceptor_mock,
            input_callback_mock.method,
            multi=False,
            accelerator_idx=0)

        perceptor_node.add_child_perceptor("child")

        assert len(perceptor_node.get_child_perceptors()) == 1
        assert perceptor_node.get_child_perceptors()[0] == "child"

    def test_remove_child_perceptor_removes_perceptor_from_children(self):
        input_callback_mock = Mock()
        perceptor_mock = PerceptorMock(sleep=0)
        perceptor_node = PerceptorNode(
            "parent",
            perceptor_mock,
            input_callback_mock.method,
            multi=False,
            accelerator_idx=0)

        perceptor_node.add_child_perceptor("child")
        assert len(perceptor_node.get_child_perceptors()) == 1

        perceptor_node.remove_child_perceptor("child")
        assert len(perceptor_node.get_child_perceptors()) == 0

    def test_add_child_perceptor_fails_when_perceptor_name_is_none(self):
        input_callback_mock = Mock()
        perceptor_mock = PerceptorMock(sleep=0)
        perceptor_node = PerceptorNode(
            "parent",
            perceptor_mock,
            input_callback_mock.method,
            multi=False,
            accelerator_idx=0)

        with pytest.raises(Exception) as context:
            perceptor_node.add_child_perceptor(None)

        assert "perceptor_name is required" in str(context.value)

    def test_add_child_perceptor_fails_when_perceptor_name_is_not_of_type_string(
            self):
        input_callback_mock = Mock()
        perceptor_mock = PerceptorMock(sleep=0)
        perceptor_node = PerceptorNode(
            "parent",
            perceptor_mock,
            input_callback_mock.method,
            multi=False,
            accelerator_idx=0)

        with pytest.raises(Exception) as context:
            perceptor_node.add_child_perceptor(1)

        assert "perceptor_name must be a string" in str(context.value)

    def test_get_child_perceptors_returns_list_of_child_perceptors(self):
        input_callback_mock = Mock()
        perceptor_mock = PerceptorMock(sleep=0)
        perceptor_node = PerceptorNode(
            "parent",
            perceptor_mock,
            input_callback_mock.method,
            multi=False,
            accelerator_idx=0)

        perceptor_node.add_child_perceptor("child1")
        perceptor_node.add_child_perceptor("child2")

        assert len(perceptor_node.get_child_perceptors()) == 2

    def test_run_calls_output_callback(self):
        input_callback_mock = Mock()
        output_callback_mock = Mock()
        perceptor_mock = PerceptorMock(sleep=0)
        perceptor_node = PerceptorNode(
            "parent",
            perceptor_mock,
            input_callback_mock.method,
            output_callback_mock.method,
            multi=False,
            accelerator_idx=0)

        return_value = "Hello!"
        stream_data = StreamData([1, 2, 3], 1)
        pom = PerceptionObjectModel()

        with patch.object(PerceptorMock, "run", return_value=return_value):
            perceptor_node.run(stream_data, pom)

        output_callback_mock.method.assert_called_once_with(return_value, pom)

    def test_run_returns_result_of_output_callback(self):
        input_callback_mock = Mock()
        return_value = "output_callback"
        output_callback_mock = Mock()
        output_callback_mock.method.return_value = return_value
        perceptor_mock = PerceptorMock(sleep=0)
        perceptor_node = PerceptorNode(
            "parent",
            perceptor_mock,
            input_callback_mock.method,
            output_callback_mock.method,
            multi=False,
            accelerator_idx=0)

        stream_data = StreamData([1, 2, 3], 1)
        pom = PerceptionObjectModel()

        assert perceptor_node.run(stream_data, pom) == return_value

    def test_run_returns_result_of_perceptor(self):
        input_callback_mock = Mock()
        perceptor_mock = PerceptorMock(sleep=0)
        perceptor_node = PerceptorNode(
            "parent",
            perceptor_mock,
            input_callback_mock.method,
            multi=False,
            accelerator_idx=0)

        return_value = "perceptor_result"
        stream_data = StreamData([1, 2, 3], 1)
        pom = PerceptionObjectModel()

        with patch.object(PerceptorMock, "run", return_value=return_value):
            assert perceptor_node.run(stream_data, pom) == return_value
