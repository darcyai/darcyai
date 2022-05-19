# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

from enum import Enum

class Processor(Enum):
    """
    Enum for the different processors
    """
    CORAL_EDGE_TPU = 1
    CPU = 2
