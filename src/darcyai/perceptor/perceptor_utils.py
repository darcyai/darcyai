# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

import importlib.util
import multiprocessing

from darcyai.perceptor.coral.coral_perceptor_base import CoralPerceptorBase
from darcyai.perceptor.processor import Processor
from darcyai.utils import validate, validate_not_none, validate_type

_supported_processors = None

def get_supported_processors() -> dict:
    """
    Gets the list of supported processors.

    # Returns
    `dict` - The list of supported processors.

    # Examples
    ```python
    >>> get_supported_processors()
    {<Processor.CORAL_EDGE_TPU: 1>: {'is_available': True, 'coral_tpus': [{'type': 'usb', 'path':\
    '/sys/bus/usb/devices/2-2'}]}, <Processor.CPU: 2>: {'is_available': True, 'cpu_count': 4}}
    ```
    """
    global _supported_processors
    if _supported_processors is None:
        coral_tpus = CoralPerceptorBase.list_edge_tpus()
        _supported_processors = {
            Processor.CORAL_EDGE_TPU: {
                "is_available": len(coral_tpus) > 0,
                "coral_tpus": coral_tpus,
            },
            Processor.CPU: {
                "is_available": importlib.util.find_spec("tensorflow") is not None \
                    or importlib.util.find_spec("tflite_runtime") is not None,
                "cpu_count": multiprocessing.cpu_count(),
            },
        }

    return _supported_processors

def get_perceptor_processor(processor_preference:list) -> Processor:
    """
    Gets the processor for the perceptor.

    # Arguments
    processor_preference (list): The list of preferred processors.

    # Returns
    `Processor` - The processor for the perceptor.

    # Examples
    ```python
    >>> from darcyai.perceptor.processor import Processor
    >>> processor_preference = [Processor.CORAL_EDGE_TPU, Processor.CPU]
    >>> get_perceptor_processor(processor_preference)
    Processor.CORAL_EDGE_TPU
    ```
    """
    validate_processor_list(processor_preference)

    supported_processors = get_supported_processors()
    for processor in processor_preference:
        validate(processor in supported_processors,
                    f"processor {processor} is not valid")
        if supported_processors[processor]["is_available"]:
            return processor

    return None

def validate_processor_preference(processor_preference, model_path_required=True):
    """
    Validate the processor preference.

    # Arguments
    processor_preference: A dictionary of processor preference.
        The key is the processor. Values are dictionaries of model paths and labels.

    # Raises
    Exception: If the processor preference is invalid.

    # Examples
    ```python
    >>> from darcyai.perceptor.processor import Processor
    >>> processor_preference = {
            Processor.CORAL_EDGE_TPU: {
                "model_path": "/path/to/model.tflite",
                "labels_file": "/path/to/labels.txt",
            },
            Processor.CPU: {
                "model_path": "/path/to/model.tflite",
                "labels_file": "/path/to/labels.txt",
            },
        }
    >>> validate_processor_preference(processor_preference)
    ```
    """
    validate_not_none(processor_preference, "processor_preference is required.")
    validate_type(processor_preference, dict, "processor_preference must be a dictionary.")
    validate(len(processor_preference) > 0, "processor_preference must not be empty.")

    for processor, processor_preference_dict in processor_preference.items():
        validate_type(processor, Processor, "processor must be a Processor.")
        validate_type(processor_preference_dict,
                      dict,
                      "processor_preference_dict must be a dictionary.")

        if model_path_required:
            if "model_path" not in processor_preference_dict:
                raise Exception("The model path is required for the processor preference")
            else:
                validate_type(
                    processor_preference_dict["model_path"], str, "model_path must be a string.")

        if "labels" in processor_preference_dict:
            validate_type(
                processor_preference_dict["labels"], dict, "labels must be a dictionary.")

        if "labels_file" in processor_preference_dict:
            validate_type(
                processor_preference_dict["labels_file"], str, "labels_file must be a string.")

def validate_processor_list(processor_list):
    """
    Validate the processor list.

    # Arguments
    processor_list: A list of processors.

    # Raises
    Exception: If the processor preference is invalid.

    # Examples
    ```python
    >>> from darcyai.perceptor.processor import Processor
    >>> processor_list = [Processor.CORAL_EDGE_TPU, Processor.CPU]
    >>> validate_processor_list(processor_list)
    ```
    """
    validate_not_none(processor_list, "processor_list is required.")
    validate_type(processor_list, list, "processor_list must be a list.")
    validate(len(processor_list) > 0, "processor_list must not be empty.")

    for processor in processor_list:
        validate_type(processor, Processor, "processor must be a Processor.")
