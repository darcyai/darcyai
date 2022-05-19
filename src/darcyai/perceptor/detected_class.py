# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

class Class:
    """
    Class to store detected class information.

    # Arguments
    class_id (int): The class ID.
    name (str): The class name.
    confidence (float): The confidence of the class.
    """

    def __init__(self, class_id, name, confidence):
        self.class_id = class_id
        self.name = name
        self.confidence = confidence

    def __str__(self):
        """
        Returns a string representation of the class.

        # Returns
        str: The string representation of the class.
        """
        return f"Class(class_id={self.class_id}, name={self.name}, confidence={self.confidence})"
