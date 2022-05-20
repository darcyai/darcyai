# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

from typing import List, Any


class EventEmitter():
    """
    Base class for all event emitter objects.
    """

    def __init__(self):
        self.__event_names = []
        self.__event_handlers = {}

    def set_event_names(self, event_names: List[str]) -> None:
        """
        Sets the event names.

        # Arguments
        event_names (list): The event names.
        """
        self.__event_names = event_names

    def get_event_names(self) -> List[str]:
        """
        Gets the event names.

        # Returns
        List[str]: The event names.
        """
        return self.__event_names

    def get_event_handlers(self, event_name: str) -> List[callable]:
        """
        Gets the event handlers.

        # Arguments
        event_name (str): The event name.

        # Returns
        List[callable]: The event handlers.
        """
        if event_name not in self.__event_handlers:
            return []

        return self.__event_handlers[event_name]

    def on(self, event_name: str, handler: callable) -> None:
        """
        Adds an event handler.

        # Arguments
        event_name (str): The event name.
        handler (callable): The handler function.
        """
        if event_name not in self.__event_names:
            raise Exception(f"Event name '{event_name}' is not valid.")

        if event_name not in self.__event_handlers:
            self.__event_handlers[event_name] = []

        self.__event_handlers[event_name].append(handler)

    def off(self, event_name: str) -> None:
        """
        Removes an event handler.

        # Arguments
        event_name (str): The event name.
        """
        if event_name not in self.__event_names:
            raise Exception(f"Event name '{event_name}' is not valid.")

        if event_name not in self.__event_handlers:
            return

        del self.__event_handlers[event_name]

    def emit(self, event_name: str, *args, **kwargs) -> Any:
        """
        Emits an event.

        # Arguments
        event_name (str): The event name.
        *args (list): The arguments.
        **kwargs (dict): The keyword arguments.
        """
        if event_name not in self.__event_handlers:
            return

        for handler in self.__event_handlers[event_name]:
            handler(*args, **kwargs)
