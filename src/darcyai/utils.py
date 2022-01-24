import time
from typing import Any


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
