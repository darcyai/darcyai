# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

from typing import Any, Union, List

from darcyai.config import Config
from darcyai.config_registry import ConfigRegistry
from darcyai.perceptor.perceptor import Perceptor
from darcyai.perceptor.perceptor_utils import get_perceptor_processor
from darcyai.perceptor.processor import Processor

class MultiPlatformPerceptorBase(Perceptor):
    """
    MultiPlatformPerceptorBase is a class that implements the Perceptor interface
    for multi-platform use.
    """
    def __init__(self, processor_preference:list=None):
        super().__init__(model_path="")

        try:
            self.processor = get_perceptor_processor(processor_preference)
        except Exception:
            self.processor = get_perceptor_processor([Processor.CORAL_EDGE_TPU, Processor.CPU])

        if self.processor is None:
            raise Exception("No processor found")

    def run(self, input_data: Any, config: ConfigRegistry = None) -> Any:
        return self.perceptor.run(input_data, config)

    def load(self, accelerator_idx: Union[int, None] = None) -> None:
        return self.perceptor.load(accelerator_idx)

    def is_loaded(self) -> bool:
        return self.perceptor.is_loaded()

    def set_loaded(self, loaded: bool) -> None:
        self.perceptor.set_loaded(loaded)

    def set_config_value(self, key: str, value: Any):
        self.perceptor.set_config_value(key, value)

    def get_config_value(self, key: str) -> Any:
        return self.perceptor.get_config_value(key)

    def init_config_registry(self):
        self.perceptor.init_config_registry()

    def get_config_schema(self) -> List[Config]:
        return self.perceptor.get_config_schema()

    def get_event_names(self) -> List[str]:
        return self.perceptor.get_event_names()

    def on(self, event_name: str, handler: callable) -> None:
        self.perceptor.on(event_name, handler)

    def off(self, event_name: str) -> None:
        self.perceptor.off(event_name)

    def emit(self, event_name: str, *args, **kwargs) -> Any:
        return self.perceptor.emit(event_name, *args, **kwargs)

    def set_event_names(self, event_names) -> None:
        self.perceptor.set_event_names(event_names)

    def set_config_schema(self, config_schema) -> None:
        self.perceptor.set_config_schema(config_schema)
