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
