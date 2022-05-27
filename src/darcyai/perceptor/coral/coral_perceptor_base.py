# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

import importlib.util
from typing import Union

from darcyai.perceptor.perceptor import Perceptor
from darcyai.utils import validate_type, validate, import_module

class CoralPerceptorBase(Perceptor):
    """
    Base class for all Coral Perceptors.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.__edgetpu = import_module("pycoral.utils.edgetpu")
        edge_tpus = self.__edgetpu.list_edge_tpus()
        if len(edge_tpus) == 0:
            raise RuntimeError("No Coral Edge TPUs found")

    def load(self, accelerator_idx: Union[int, None] = None) -> None:
        """
        Loads the perceptor.

        # Arguments
        accelerator_idx (int, None): The index of the accelerator to load
            the perceptor on. Defaults to `None`.
        """
        if accelerator_idx is None:
            device = None
        else:
            validate_type(accelerator_idx, int, "accelerator_idx must be an integer")
            validate(accelerator_idx >= 0, "accelerator_idx must be greater than or equal to 0")
            device = f":{accelerator_idx}"

        if device is None:
            self.interpreter = self.__edgetpu.make_interpreter(self.model_path)
        else:
            self.interpreter = self.__edgetpu.make_interpreter(
                self.model_path,
                device=f":{accelerator_idx}")

        self.interpreter.allocate_tensors()

    @staticmethod
    def list_edge_tpus() -> list:
        """
        Lists the Coral Edge TPUs.

        # Returns
        list: The Coral Edge TPUs.

        # Example
        ```python
        >>> from darcyai.perceptor.coral.coral_perceptor_base import CoralPerceptorBase
        >>> CoralPerceptorBase.list_edge_tpus()
        ["/device:coral:0"]
        ```
        """
        tpus = []
        try:
            if importlib.util.find_spec("pycoral.utils.edgetpu") is not None:
                edgetpu = import_module("pycoral.utils.edgetpu")
                tpus = edgetpu.list_edge_tpus()
        except Exception:
            pass

        return tpus
