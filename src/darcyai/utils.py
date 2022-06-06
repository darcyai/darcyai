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

import time
from importlib import import_module as import_helper
from typing import Any

imported_modules = {}

def validate_not_none(value: Any, message: str) -> None:
    """
    Validates that the value is not None.

    # Arguments
    value (Any): the value to validate
    message (str): the message to raise if the value is None
    """
    validate(value is not None, message)


def validate_type(value: Any, clazz: Any, message: str) -> None:
    """
    Validates that the value is of the specified type.

    # Arguments
    value (Any): the value to validate
    clazz (Any): the class to validate the value against
    message (str): the message to raise if the value is not of the specified type
    """
    validate(isinstance(value, clazz), message)


def validate(condition: bool, message: str) -> None:
    """
    Validates that the condition is true.

    # Arguments
    condition (bool): the condition to validate
    message (str): the message to raise if the condition is false
    """
    if condition is None or not condition:
        raise Exception(message)


def timestamp() -> int:
    """
    Returns the current timestamp in milliseconds.

    # Returns
    int: the current timestamp in milliseconds
    """
    return int(time.time() * 1000)

def import_module(name: str) -> Any:
    """
    Imports the specified module.

    # Arguments
    name (str): the name of the module to import

    # Returns
    Any: the imported module
    """
    if name in imported_modules:
        return imported_modules[name]

    module = import_helper(name)
    imported_modules[name] = module

    return module
