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
