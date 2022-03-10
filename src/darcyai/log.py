import logging
import logging_json
import os


def setup_custom_logger(name):
    """
    Setup a custom logger for the DarcyAI.

    # Arguments
    name (str): The name of the logger.

    # Returns
    logger (logging.Logger): The logger.
    """
    formatter = logging_json.JSONFormatter(fields={
        "timestamp": "asctime",
        "level": "levelname",
        "thread": "threadName",
        "module": "module",
    })

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    log_level = os.environ.get("DARCYAI_LOG_LEVEL", "INFO").upper()
    logger.setLevel(log_level)
    logger.addHandler(handler)

    return logger
