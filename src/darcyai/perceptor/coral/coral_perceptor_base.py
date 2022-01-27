from importlib import import_module
from typing import Union

from darcyai.perceptor.perceptor import Perceptor
from darcyai.utils import validate_type, validate

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
