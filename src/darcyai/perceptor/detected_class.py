class Class:
    """
    Class to store detected class information.
    """

    def __init__(self, class_id, name, confidence):
        """
        Constructor.

        Arguments:
            class_id (int): The class ID.
            name (str): The class name.
            confidence (float): The confidence of the class.
        """
        self.class_id = class_id
        self.name = name
        self.confidence = confidence

    def __str__(self):
        """
        Returns a string representation of the class.

        Returns:
            str: The string representation of the class.
        """
        return f"Class(class_id={self.class_id}, name={self.name}, confidence={self.confidence})"