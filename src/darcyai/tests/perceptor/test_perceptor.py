# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

import pytest

from darcyai.perceptor.perceptor import Perceptor


class TestPerceptor:
    """
    Perceptor tests.
    """
    def test_init_happy_path(self):
        perceptor = Perceptor(model_path="model.tflite")
        assert perceptor is not None

    def test_init_throws_when_model_path_is_none(self):
        with pytest.raises(Exception) as context:
            _ = Perceptor(model_path=None)

        assert "model_path is required" in str(context.value)

    def test_is_loaded_returns_false_when_model_is_not_loaded(self):
        perceptor = Perceptor(model_path="model.tflite")
        assert perceptor.is_loaded() is False

    def test_is_loaded_returns_true_when_model_is_loaded(self):
        perceptor = Perceptor(model_path="model.tflite")
        perceptor.set_loaded(True)
        assert perceptor.is_loaded() is True

    def test_set_loaded_sets_loaded_to_true(self):
        perceptor = Perceptor(model_path="model.tflite")
        perceptor.set_loaded(True)
        assert perceptor.is_loaded() is True

    def test_set_loaded_throws_when_loaded_is_not_boolean(self):
        perceptor = Perceptor(model_path="model.tflite")
        with pytest.raises(Exception) as context:
            perceptor.set_loaded("not a boolean")

        assert "loaded must be a boolean" in str(context.value)

    def test_set_loaded_throws_when_loaded_is_none(self):
        perceptor = Perceptor(model_path="model.tflite")
        with pytest.raises(Exception) as context:
            perceptor.set_loaded(None)

        assert "loaded is required" in str(context.value)
