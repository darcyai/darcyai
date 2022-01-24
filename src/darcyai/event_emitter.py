from typing import List, Any


class EventEmitter():
    """
    Base class for all event emitter objects.
    """

    def __init__(self):
        self.event_names = []
        self.event_handlers = {}

    def get_event_names(self) -> List[str]:
        """
        Gets the event names.

        # Returns
        List[str]: The event names.
        """
        return self.event_names

    def on(self, event_name: str, handler: callable) -> None:
        """
        Adds an event handler.

        # Arguments
        event_name (str): The event name.
        handler (callable): The handler function.
        """
        if event_name not in self.event_names:
            raise Exception(f"Event name '{event_name}' is not valid.")

        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []

        self.event_handlers[event_name].append(handler)

    def off(self, event_name: str) -> None:
        """
        Removes an event handler.

        # Arguments
        event_name (str): The event name.
        """
        if event_name not in self.event_names:
            raise Exception(f"Event name '{event_name}' is not valid.")

        if event_name not in self.event_handlers:
            return

        del self.event_handlers[event_name]

    def emit(self, event_name: str, *args, **kwargs) -> Any:
        """
        Emits an event.

        # Arguments
        event_name (str): The event name.
        *args (list): The arguments.
        **kwargs (dict): The keyword arguments.
        """
        if event_name not in self.event_handlers:
            return

        for handler in self.event_handlers[event_name]:
            handler(*args, **kwargs)
