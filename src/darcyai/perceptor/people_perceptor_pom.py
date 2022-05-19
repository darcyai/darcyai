# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

# pylint: skip-file
from collections import OrderedDict

from darcyai.serializable import Serializable

class PeoplePOM(Serializable):
    """
    People perceptor object model
    """
    def __init__(self):
        super().__init__()
        self.__people = OrderedDict()
        self.__annotated_frame = None
        self.__raw_frame = None

    def set_annotated_frame(self, frame):
        """
        Stores the frame annotated with the persons data

        # Arguments
            frame (np.array): The annotated frame
        """
        self.__annotated_frame = frame
    
    def set_raw_frame(self, frame):
        """
        Stores the frame with the people data

        # Arguments
            frame (np.array): The raw frame
        """
        self.__raw_frame = frame

    def set_people(self, people):
        """
        Stores the detected people

        # Arguments
            people (list): The detected people
        """
        self.__people = people

    def annotatedFrame(self):
        """
        Returns the annotated frame

        # Returns
            np.array: The annotated frame
        """
        return self.__annotated_frame

    def rawFrame(self):
        """
        Returns the raw frame

        # Returns
            np.array: The raw frame
        """
        return self.__raw_frame

    def peopleCount(self):
        """
        Returns the number of people detected

        # Returns
            int: The number of people detected
        """
        return len(self.__people)

    def personInFront(self):
        """
        Returns the person in front of the camera

        # Returns
            The person in front of the camera
        """
        poi = None
        for person in self.__people:
            if self.__people[person]["is_poi"]:
                poi = self.__people[person]
                break

        return poi

    def people(self):
        """
        Returns the detected people

        # Returns
            list: The detected people
        """
        return self.__people

    def person(self, person_id):
        """
        Returns the person with the given id

        # Arguments
            person_id (str): The person id

        # Returns
            dict: The person
        """
        if person_id in self.__people:
            return self.__people[person_id]
        else:
            return None

    def faceImage(self, person_id):
        """
        Returns the face image of the person with the given id

        # Arguments
            person_id (str): The person id

        # Returns
            np.array: The face image
        """
        if not self.__people[person_id]["has_face"]:
            return None

        frame_copy = self.__raw_frame.copy()
        (x0, y0), (x1, y1) = self.__people[person_id]["face_rectangle"]
        frame_width = frame_copy.shape[1]
        frame_height = frame_copy.shape[0]

        if x0 < 0:
            x0 = 0

        if y0 < 0:
            y0 = 0

        if x1 > frame_width:
            x1 = frame_width

        if y1 > frame_height:
            y1 = frame_height

        face = frame_copy[y0:y1, x0:x1]
        return face

    def bodyImage(self, person_id):
        """
        Returns the body image of the person with the given id
        
        # Arguments
            person_id (str): The person id

        # Returns
            np.array: The body image
        """
        if not self.__people[person_id]["has_body"]:
            return None

        frame_copy = self.__raw_frame.copy()
        (x0, y0), (x1, y1) = self.__people[person_id]["body_rectangle"]
        frame_width = frame_copy.shape[1]
        frame_height = frame_copy.shape[0]

        if x0 < 0:
            x0 = 0

        if y0 < 0:
            y0 = 0

        if x1 > frame_width:
            x1 = frame_width

        if y1 > frame_height:
            y1 = frame_height

        body = frame_copy[y0:y1, x0:x1]
        return body

    def personImage(self, person_id):
        """
        Returns the image of the person with the given id

        # Arguments
            person_id (str): The person id

        # Returns
            np.array: The person image
        """
        if not self.__people[person_id]["has_body"] or not self.__people[person_id]["has_face"]:
            return None

        frame_copy = self.__raw_frame.copy()
        (bx0, by0), (bx1, by1) = self.__people[person_id]["body_rectangle"]
        (fx0, fy0), (fx1, fy1) = self.__people[person_id]["face_rectangle"]
        frame_width = frame_copy.shape[1]
        frame_height = frame_copy.shape[0]

        if bx0 < 0:
            bx0 = 0

        if by0 < 0:
            by0 = 0

        if bx1 > frame_width:
            bx1 = frame_width

        if by1 > frame_height:
            by1 = frame_height

        if fx0 < 0:
            fx0 = 0

        if fy0 < 0:
            fy0 = 0

        if fx1 > frame_width:
            fx1 = frame_width

        if fy1 > frame_height:
            fy1 = frame_height

        x0 = 0
        x1 = 0
        y0 = 0
        y1 = 0

        if bx0 < fx0:
            x0 = bx0
        else:
            x0 = fx0

        if by0 < fy0:
            y0 = by0
        else:
            y0 = fy0

        if bx1 > fx1:
            x1 = bx1
        else:
            x1 = fx1

        if by1 > fy1:
            y1 = by1
        else:
            y1 = fy1

        image = frame_copy[y0:y1, x0:x1]
        return image

    def faceSize(self, person_id):
        """
        Returns the size of the face of the person with the given id

        # Arguments
            person_id (str): The person id

        # Returns
            int: The size of the face
        """
        if not self.__people[person_id]["has_face"]:
            return 0

        rectangle = self.__people[person_id]["face_rectangle"]
        width = rectangle[1][0] - rectangle[0][0]
        height = rectangle[1][1] - rectangle[0][1]
        return (width, height)

    def bodySize(self, person_id):
        """
        Returns the size of the body of the person with the given id

        # Arguments
            person_id (str): The person id

        # Returns
            int: The size of the body
        """
        if not self.__people[person_id]["has_body"]:
            return 0

        rectangle = self.__people[person_id]["body_rectangle"]
        width = rectangle[1][0] - rectangle[0][0]
        height = rectangle[1][1] - rectangle[0][1]
        return (width, height)

    def wholeSize(self, person_id):
        """
        Returns the size of the whole person with the given id

        # Arguments
            person_id (str): The person id

        # Returns
            int: The size of the whole person
        """
        if not self.__people[person_id]["has_body"] or not self.__people[person_id]["has_face"]:
            return 0

        body_size = self.bodySize(person_id)
        face_size = self.faceSize(person_id)
        return ((body_size[0] + face_size[0]), (body_size[1] + face_size[1]))

    def bodyPose(self, person_id):
        """
        Returns the PoseNet data of the person with the given id

        # Arguments
            person_id (str): The person id

        # Returns
            The PoseNet data
        """
        return self.__people[person_id]["pose"]

    def bodyPoseHistory(self, person_id):
        """
        Returns the PoseNet data history of the person with the given id
            
        # Arguments
            person_id (str): The person id

        # Returns
            The PoseNet data
        """
        return None

    def travelPath(self, person_id):
        """
        Returns the travel path of the person with the given id

        # Arguments
            person_id (str): The person id

        # Returns
            The travel path
        """
        return None

    def timeInView(self, person_id):
        """
        Returns the time the person with the given id has been in view

        # Arguments
            person_id (str): The person id

        # Returns
            int: The time in view
        """
        return 0
    
    def recentlyDepartedPeople(self):
        """
        Returns the people that have recently departed

        # Returns
            list: The people that have recently departed
        """
        return []
    
    def occludedPeople(self):
        """
        Returns the people that are occluded

        # Returns
            list: The people that are occluded
        """
        return []

    def serialize(self):
        """
        Returns the serialized data of the object

        # Returns
            dict: The serialized data
        """
        return {
            "people_count": self.peopleCount(),
            "people_on_current_frame": [person_id for person_id in self.__people],
        }