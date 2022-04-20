class Object:
    """
    Class for storing detected objects.
    """

    def __init__(self, class_id, name, confidence, xmin, ymin, xmax, ymax):
        """
        Constructor.

        Arguments:
            class_id (int): The class ID.
            name (str): The class name.
            confidence (float): The confidence of the class.
            xmin (int): The x-coordinate of the top left corner of the bounding box.
            ymin (int): The y-coordinate of the top left corner of the bounding box.
            xmax (int): The x-coordinate of the bottom right corner of the bounding box.
            ymax (int): The y-coordinate of the bottom right corner of the bounding box.
        """
        self.class_id = class_id
        self.name = name
        self.confidence = confidence
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
