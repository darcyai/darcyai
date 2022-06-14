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

import cv2
import collections
import enum
import importlib.util
import math
import numpy as np
import os
import platform
import time
import uuid

from collections import OrderedDict
from darcyai.config import Config, RGB
from darcyai.perceptor.perceptor import Perceptor
from darcyai.utils import import_module

from .people_perceptor_pom import PeoplePOM


class KeypointType(enum.IntEnum):
    """Pose kepoints."""
    NOSE = 0
    LEFT_EYE = 1
    RIGHT_EYE = 2
    LEFT_EAR = 3
    RIGHT_EAR = 4
    LEFT_SHOULDER = 5
    RIGHT_SHOULDER = 6
    LEFT_ELBOW = 7
    RIGHT_ELBOW = 8
    LEFT_WRIST = 9
    RIGHT_WRIST = 10
    LEFT_HIP = 11
    RIGHT_HIP = 12
    LEFT_KNEE = 13
    RIGHT_KNEE = 14
    LEFT_ANKLE = 15
    RIGHT_ANKLE = 16


Point = collections.namedtuple("Point", ["x", "y"])
Point.distance = lambda a, b: math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)
Point.distance = staticmethod(Point.distance)

Keypoint = collections.namedtuple("Keypoint", ["point", "score"])

Pose = collections.namedtuple("Pose", ["keypoints", "score"])


class PoseEngine():
    """Engine used for pose tasks."""
    _EDGETPU_SHARED_LIB = {
        "Linux": "libedgetpu.so.1",
        "Darwin": "libedgetpu.1.dylib",
        "Windows": "edgetpu.dll"
    }[platform.system()]
    _POSENET_SHARED_LIB = {
        "Linux": "posenet_decoder.so",
        "Darwin": "posenet_decoder.so",
        "Windows": "posenet_decoder.dll"
    }[platform.system()]

    def __init__(self,
                 model_path,
                 mirror=False,
                 arch=platform.uname().machine,
                 tpu: bool = True,
                 num_cpu_threads: int = 1):
        """
        Creates a PoseEngine with given model.

        # Arguments
        model_path: String, path to TF-Lite Flatbuffer file.
        mirror: Flip keypoints horizontally.
        arch: Architecture of the device.
        tpu: Whether to use TPU or CPU.
        num_cpu_threads: Number of CPU threads to use.
        """

        if arch == "AMD64":
            arch = "x86_64"

        script_dir = os.path.dirname(os.path.realpath(__file__))

        sysname = platform.uname().system.lower()
        posenet_shared_lib = os.path.join(
            script_dir, "posenet_lib", arch, sysname, PoseEngine._POSENET_SHARED_LIB)

        if not os.path.exists(posenet_shared_lib):
            raise ValueError(f"Posenet library not found at {posenet_shared_lib}")

        if importlib.util.find_spec("tflite_runtime") is not None:
            tf = import_module("tflite_runtime.interpreter")
            load_delegate = tf.load_delegate
            interpreter = tf.Interpreter
        else:
            tf = import_module("tensorflow")
            load_delegate = tf.lite.experimental.load_delegate
            interpreter = tf.lite.Interpreter

        posenet_decoder_delegate = load_delegate(posenet_shared_lib)
        delegates = [posenet_decoder_delegate]

        if tpu:
            self.__edgetpu = import_module("pycoral.utils.edgetpu")
            edgetpu_delegate = load_delegate(PoseEngine._EDGETPU_SHARED_LIB)
            delegates.append(edgetpu_delegate)

        self._interpreter = interpreter(
            model_path, experimental_delegates=delegates, num_threads=num_cpu_threads)
        self._interpreter.allocate_tensors()

        self._mirror = mirror

        self._input_tensor_shape = self.get_input_tensor_shape()
        if (self._input_tensor_shape.size != 4 or
                self._input_tensor_shape[3] != 3 or
                self._input_tensor_shape[0] != 1):
            raise ValueError(
                ("Image model should have input shape [1, height, width, 3]!"
                 f" This model has {self._input_tensor_shape}."))
        _, self._input_height, self._input_width, self._input_depth = self.get_input_tensor_shape()
        self._input_type = self._interpreter.get_input_details()[0]["dtype"]
        self._inf_time = 0
        self.__tpu = tpu

    def run_inference(self, input_data):
        """
        Run inference using the zero copy feature from pycoral and returns inference time in ms.
        """
        start = time.monotonic()
        if not self.__tpu:
            self._interpreter.set_tensor(self._interpreter.get_input_details()[0]["index"],
                                         input_data)
            self._interpreter.invoke()
        else:
            self.__edgetpu.run_inference(self._interpreter, input_data)
        self._inf_time = time.monotonic() - start
        return self._inf_time * 1000

    def detect_poses_in_image(self, img):
        """
        Detects poses in a given image.
        For ideal results make sure the image fed to this function is close to the
        expected input size - it is the caller's responsibility to resize the
        image accordingly.

        # Arguments
        img: numpy array containing image
        """

        # Extend or crop the input to match the input shape of the network.
        if img.shape[0] < self._input_height or img.shape[1] < self._input_width:
            img = np.pad(img, [[0, max(0, self._input_height - img.shape[0])],
                               [0, max(0, self._input_width - img.shape[1])], [0, 0]],
                         mode="constant")
        img = img[0:self._input_height, 0:self._input_width]
        assert img.shape == tuple(self._input_tensor_shape[1:])

        input_data = np.expand_dims(img, axis=0)
        if self._input_type is np.float32:
            # Floating point versions of posenet take image data in [-1,1] range.
            input_data = np.float32(img) / 128.0 - 1.0
        else:
            # Assuming to be uint8
            input_data = np.asarray(img)

        if not self.__tpu:
            input_data = np.expand_dims(input_data, axis=0)
        else:
            input_data = input_data.flatten()

        self.run_inference(input_data)

        return self.parse_output()

    def get_input_tensor_shape(self):
        """Returns input tensor shape."""
        return self._interpreter.get_input_details()[0]["shape"]

    def get_output_tensor(self, idx):
        """Returns output tensor view."""
        return np.squeeze(self._interpreter.tensor(
            self._interpreter.get_output_details()[idx]["index"])())

    def parse_output(self):
        """Parses interpreter output tensors and returns decoded poses."""
        keypoints = self.get_output_tensor(0)
        keypoint_scores = self.get_output_tensor(1)
        pose_scores = self.get_output_tensor(2)
        num_poses = self.get_output_tensor(3)
        poses = []
        for i in range(int(num_poses)):
            pose_score = pose_scores[i]
            pose_keypoints = {}
            for j, point in enumerate(keypoints[i]):
                y, x = point
                if self._mirror:
                    y = self._input_width - y
                pose_keypoints[KeypointType(j)] = Keypoint(
                    Point(x, y), keypoint_scores[i, j])
            poses.append(Pose(pose_keypoints, pose_score))
        return poses, self._inf_time


class PeoplePerceptorBase(Perceptor):
    """
    Base class for people perception.
    """
    def __init__(self):
        super().__init__(model_path="")

        self.set_config_schema([
            Config("minimum_face_threshold",
                   "Minimum Face Threshold",
                   "float",
                   0.4,
                   "Confidence threshold for detecting the face as a percent certainty"),
            Config("minimum_body_threshold",
                   "Minimum Body Threshold",
                   "float",
                   0.2,
                   "Confidence threshold for detecting the body as a percent certainty"),
            Config("minimum_face_height",
                   "Minimum Face Height",
                   "int",
                   20,
                   "The minimum height of the persons face in pixels that we want to work with"),
            Config("minimum_body_height",
                   "Minimum Body Height",
                   "int",
                   120,
                   "The minimum height of the persons body in pixels that we want to work with"),
            Config("show_pose_landmark_dots",
                   "Show pose landmark dots",
                   "bool",
                   False,
                   "Show pose landmark dots (nose, ears, elbows, etc.)"),
            Config("show_body_rectangle",
                   "Show body rectangle",
                   "bool",
                   False,
                   "Draw a rectangle around the persons body"),
            Config("show_face_rectangle",
                   "Show face rectangle",
                   "bool",
                   False,
                   "Draw a rectangle around the persons face"),
            Config("face_rectangle_color",
                   "Face rectangle color",
                   "rgb",
                   RGB(255, 0, 0),
                   "Color of the face rectangle"),
            Config("face_rectangle_thickness",
                   "Face rectangle thickness",
                   "int",
                   1,
                   "Thickness of the face rectangle"),
            Config("body_rectangle_color",
                   "Body rectangle color",
                   "rgb",
                   RGB(0, 255, 0),
                   "Color of the body rectangle"),
            Config("body_rectangle_thickness",
                   "Body rectangle thickness",
                   "int",
                   1,
                   "Thickness of the body rectangle"),
            Config("pose_landmark_dot_confidence_threshold",
                   "Pose landmark dot confidence threshold",
                   "float",
                   0.5,
                   "Confidence threshold for identifying pose landmarks as a percent certainty"),
            Config("pose_landmark_dot_size",
                   "Pose landmark dot size",
                   "int",
                   1,
                   "Size of the pose landmark dots"),
            Config("pose_landmark_dot_color",
                   "Pose landmark dot color",
                   "rgb",
                   RGB(255, 255, 255),
                   "Color of the pose landmark dots"),
            Config("show_face_position_arrow",
                   "Show face position arrow",
                   "bool",
                   False,
                   "Show the arrow that indicates which direction the person is looking"),
            Config("face_position_arrow_color",
                   "Face position arrow color",
                   "rgb",
                   RGB(255, 255, 255),
                   "Color of the face position arrow"),
            Config("face_position_arrow_stroke",
                   "Face position arrow stroke",
                   "int",
                   1,
                   "Thickness of the face position arrow"),
            Config("face_position_arrow_offset_x",
                   "Face position arrow offset x",
                   "int",
                   0,
                   "X offset for the face position arrow"),
            Config("face_position_arrow_offset_y",
                   "Face position arrow offset y",
                   "int",
                   -30,
                   "Y offset for the face position arrow"),
            Config("face_position_arrow_length",
                   "Face position arrow length",
                   "int",
                   20,
                   "Length of the face position arrow"),
            Config("face_position_left_right_threshold",
                   "Face position left/right threshold",
                   "float",
                   0.3,
                   "Threshold for detecting if the person is looking left or right"),
            Config("face_position_straight_threshold",
                   "Face position straight threshold",
                   "float",
                   0.7,
                   "Threshold for detecting if the person is looking straight"),
            Config("show_forehead_center_dot",
                   "Show forehead center dot",
                   "bool",
                   False,
                   "Show a dot in the center of the persons forehead"),
            Config("forehead_center_dot_color",
                   "Forehead center dot color",
                   "rgb",
                   RGB(255, 255, 255),
                   "Color of the forehead center dot"),
            Config("forehead_center_dot_size",
                   "Forehead center dot size",
                   "int",
                   1,
                   "Size of the forehead center dot"),
            Config("face_rectangle_y_factor",
                   "Face rectangle Y factor",
                   "float",
                   1.0,
                   "Size adjustment factor for the height of the persons face, which can be used \
                       to make sure objects like hair and hats are captured"),
            Config("show_centroid_dots",
                   "Show centroid information",
                   "bool",
                   False,
                   "Show centroid information (center of the face or body)"),
            Config("centroid_dots_color",
                   "Centroid information color",
                   "rgb",
                   RGB(255, 255, 255),
                   "Color of the centroid information"),
            Config("centroid_dots_size",
                   "Centroid information size",
                   "int",
                   1,
                   "Size of the centroid information"),
            Config("object_tracking_allowed_missed_frames",
                   "Object tracking allowed missed frames",
                   "int",
                   50,
                   "Object tracking allowed missed frames"),
            Config("object_tracking_color_sample_pixels",
                   "Object tracking color sample pixels",
                   "int",
                   4,
                   "Number of pixels to use for color sampling when tracking objects"),
            Config("object_tracking_info_history_count",
                   "Object tracking info history count",
                   "int",
                   3,
                   "Number of video frames used to track an object in the field of view"),
            Config("object_tracking_removal_count",
                   "Object tracking removal count",
                   "int",
                   50,
                   "Number of frames to wait before removing an object from tracking"),
            Config("object_tracking_centroid_weight",
                   "Object tracking centroid weight",
                   "float",
                   0.25,
                   "Level of importance that centroid data has when tracking objects"),
            Config("object_tracking_color_weight",
                   "Object tracking color weight",
                   "float",
                   0.25,
                   "Level of importance that color data has when tracking objects"),
            Config("object_tracking_vector_weight",
                   "Object tracking vector weight",
                   "float",
                   0.25,
                   "Level of importance that vector data has when tracking objects"),
            Config("object_tracking_size_weight",
                   "Object tracking size weight",
                   "float",
                   0.25,
                   "Level of importance that size data has when tracking objects"),
            Config("object_tracking_creation_m",
                   "Object tracking creation M",
                   "int",
                   10,
                   "Minimum number of frames out of N frames that an object must be present in \
                       the field of view before it is tracked"),
            Config("object_tracking_creation_n",
                   "Object tracking creation N",
                   "int",
                   7,
                   "Total number of frames used to evaluate an object before it is tracked"),
            Config("person_tracking_creation_m",
                   "Person tracking creation M",
                   "int",
                   20,
                   "Minimum number of frames out of N frames needed to promote a tracked object \
                       to a person"),
            Config("person_tracking_creation_n",
                   "Person tracking creation N",
                   "int",
                   16,
                   "Total number of frames used to evaluate a tracked object before it is \
                       promoted to a person"),
            Config("show_person_id",
                   "Show person ID",
                   "bool",
                   False,
                   "Show anonymous unique identifier for the person"),
            Config("person_data_line_color",
                   "Person data line color",
                   "rgb",
                   RGB(255, 255, 255),
                   "Color of the person data line"),
            Config("person_data_line_thickness",
                   "Person data line thickness",
                   "int",
                   1,
                   "Thickness of the person data line"),
            Config("person_data_identity_text_color",
                   "Person data identity text color",
                   "rgb",
                   RGB(255, 255, 255),
                   "Color of the person data identity text"),
            Config("person_data_identity_text_stroke",
                   "Person data identity text stroke",
                   "int",
                   1,
                   "Thickness of the person data identity text"),
            Config("person_data_identity_text_font_size",
                   "Person data identity text font size",
                   "float",
                   1.0,
                   "Font size of the person data identity text"),
            Config("person_data_text_offset_x",
                   "Person data text offset X",
                   "int",
                   30,
                   "X offset of the person data text"),
            Config("person_data_text_offset_y",
                   "Person data text offset Y",
                   "int",
                   -40,
                   "Y offset of the person data text"),
            Config("identity_text_prefix",
                   "Identity text prefix",
                   "str",
                   "Person ID: ",
                   "Text information that you want to display at the beginning of the person ID"),
            Config("rolling_video_storage_frame_count",
                   "Rolling video storage frame count",
                   "int",
                   100,
                   "Number of the video frames to store while processing"),
        ])

        self.set_event_names([
            "new_person_entered_scene",
            "person_facing_new_direction",
            "new_person_in_front",
            "person_left_scene",
            "identity_determined_for_person",
            "person_got_too_close",
            "person_went_too_far_away",
            "max_person_count_reached",
            "person_count_fell_below_maximum",
            "person_occluded"
        ])

        self.__body_number = 0
        self.__body_history = OrderedDict()
        self.__body_missing = OrderedDict()
        self.__body_seen = OrderedDict()
        self.__person_data = OrderedDict()
        self.__poi = None
        self.__prior_poi_id = 0
        self.__frame_number = 0
        self.__frame_history = OrderedDict()
        self.__frame_width = 0
        self.__frame_height = 0

    def run(self, input_data, config, primary_pose_engine):
        # Start with basic frame operations
        frame = input_data
        self.__frame_number += 1
        self.__set_frame_dimensions(frame)
        self.__add_current_frame_to_rolling_history(frame, config)

        # Perform posenet primary AI inference
        poses, _ = primary_pose_engine.detect_poses_in_image(frame)

        # Create POM object
        pom = PeoplePOM()

        # Place raw frame into POM
        pom.set_raw_frame(frame.copy())

        # Pass detected poses through body qualifier
        bodies = self.__get_qualified_body_detections(poses, config)

        # Process the bodies for various attributes
        bodies = self.__process_body_attributes(bodies, frame, config)

        # Perform tracking on bodies
        self.__apply_best_object_matches_to_body_tracking_info(
            self.__frame_number, bodies, config)
        self.__mark_unmatched_body_ids_as_missing(self.__frame_number, config)

        # Check if a new POI has been determined
        if self.__poi is not None and ("person_id" in self.__poi) and self.__poi["person_id"] != 0:
            if self.__prior_poi_id != self.__poi["person_id"]:
                self.__set_person_as_poi(self.__poi["person_id"])

        # Perform cleanup on people who are not detected
        self.__process_cleanup_of_missing_bodies(config)

        # Annotate the frame as determined by configuration
        annotated_frame = self.__annotate_frame(bodies, frame.copy(), config)
        pom.set_annotated_frame(annotated_frame)

        people = OrderedDict()
        for body in bodies:
            if self.__check_if_person_data_record_exists_for_body_id(body["body_id"]):
                person_id_value = self.__person_data[body["person_id"]]["uuid"]
                body["person_uuid"] = person_id_value
                body["is_poi"] = self.__person_data[body["person_id"]]["is_poi"]
                people[person_id_value] = body
        pom.set_people(people)
        return pom

    def __set_frame_dimensions(self, frame):
        self.__frame_width = frame.shape[1]
        self.__frame_height = frame.shape[0]

    def __add_current_frame_to_rolling_history(self, frame, config):
        milltime = int(round(time.time() * 1000))
        cur_frame = {"timestamp": milltime, "frame": frame.copy()}
        self.__frame_history[self.__frame_number] = cur_frame

        if len(self.__frame_history) > config.rolling_video_storage_frame_count:
            self.__frame_history.popitem(last=False)

    def __process_body_attributes(self, bodies, frame, config):
        """
        Process the bodies for various attributes
        """
        max_face_height = 0
        body_with_max_face_height = None
        for body in bodies:
            body["face_position"] = self.__determine_face_position(
                body, config)
            body["has_forehead"] = self.__determine_if_forehead_visible(body)
            body["forehead_center"] = self.__determine_forehead_center(body)
            body["body_rectangle"] = self.__find_body_rectangle(body)
            body["face_rectangle"] = self.__find_face_rectangle(body, config)
            body["tracking_info"] = self.__generate_tracking_info_for_body(
                frame, body, config)

            if not body["has_face"]:
                continue

            cur_face_height = int(body["face_rectangle"][1][1] - body["face_rectangle"][0][1])
            if cur_face_height > max_face_height:
                max_face_height = cur_face_height
                body_with_max_face_height = body

        self.__poi = body_with_max_face_height

        return bodies

    def __annotate_frame(self, bodies, frame, config):
        """
        Annotate the frame as determined by configuration
        """
        if config.show_pose_landmark_dots:
            for body in bodies:
                frame = self.__draw_landmark_points_on_body(
                    frame, body, config)

        if config.show_face_position_arrow:
            for body in bodies:
                frame = self.__draw_face_position_arrow_on_frame(
                    frame, body, config)

        if config.show_forehead_center_dot:
            for body in bodies:
                frame = self.__draw_forehead_center_dot_on_frame(
                    frame, body, config)

        if config.show_body_rectangle:
            for body in bodies:
                frame = self.__draw_body_rectangle_on_frame(
                    frame, body, config)

        if config.show_face_rectangle:
            for body in bodies:
                frame = self.__draw_face_rectangle_on_frame(
                    frame, body, config)

        if config.show_centroid_dots:
            for body in bodies:
                frame = self.__draw_centroid_circles_on_frame(
                    frame, body, config)

        if config.show_person_id:
            for body in bodies:
                frame = self.__draw_person_data_on_frame(frame, body, config)

        return frame

    def __get_qualified_body_detections(self, poses, config):
        """
        Qualify the body detections based on the configuration
        """
        bodies = []

        for pose in poses:
            cur_body = {}
            meets_confidence = False
            meets_size = False
            cur_body["person_id"] = 0
            cur_body["has_face"] = False
            cur_body["has_body"] = False
            cur_body["has_forehead"] = False
            cur_body["face_score"] = 0.0
            cur_body["body_score"] = 0.0
            cur_body["body_rectangle"] = ((0, 0), (0, 0))
            cur_body["face_rectangle"] = ((0, 0), (0, 0))
            cur_body["body_id"] = 0

            # Compute the confidence scores for face and body separately
            face_score = (pose.keypoints[0].score + pose.keypoints[1].score +
                          pose.keypoints[2].score + pose.keypoints[3].score +
                          pose.keypoints[4].score) / 5
            body_score = (pose.keypoints[5].score + pose.keypoints[6].score +
                          pose.keypoints[7].score + pose.keypoints[8].score +
                          pose.keypoints[9].score + pose.keypoints[10].score +
                          pose.keypoints[11].score +
                          pose.keypoints[12].score +
                          pose.keypoints[13].score + pose.keypoints[14].score +
                          pose.keypoints[15].score + pose.keypoints[16].score) / 12

            # Evaluate confidence levels first
            if face_score >= config.minimum_face_threshold:
                meets_confidence = True
                cur_body["has_face"] = True
                cur_body["face_score"] = face_score

            if body_score >= config.minimum_body_threshold:
                meets_confidence = True
                cur_body["has_body"] = True
                cur_body["body_score"] = body_score

            # Now check for size requirements
            if meets_confidence:
                # Get face and body sizes from keypoint coordinates in rough estimate style
                face_height = ((pose.keypoints[5].point[1] + pose.keypoints[6].point[1]) / 2) - \
                    ((pose.keypoints[1].point[1] +
                     pose.keypoints[2].point[1]) / 2)
                body_height = ((pose.keypoints[15].point[1] + pose.keypoints[16].point[1]) / 2) - \
                    pose.keypoints[0].point[1]

                if face_height >= config.minimum_face_height:
                    meets_size = True
                    cur_body["simple_face_height"] = face_height

                if body_height >= config.minimum_body_height:
                    meets_size = True
                    cur_body["simple_body_height"] = body_height

                # If we meet both size and confidence requirements, put this body in the output set
                if meets_size:
                    cur_body["pose"] = pose
                    bodies.append(cur_body)

        return bodies

    def __draw_face_position_arrow_on_frame(self, frame, body, config):
        """
        Draw an arrow on the frame indicating the face position
        """
        nose_x = body["pose"].keypoints[0].point[0]
        nose_y = body["pose"].keypoints[0].point[1]

        start_point = (0, 0)
        end_point = (0, 0)

        if body["face_position"] == "Straight":
            start_y = nose_y - (config.face_position_arrow_length / 2) + \
                config.face_position_arrow_offset_y
            end_y = nose_y + (config.face_position_arrow_length / 2) + \
                config.face_position_arrow_offset_y
            start_x = nose_x + config.face_position_arrow_offset_x
            end_x = nose_x + config.face_position_arrow_offset_x
            start_point = (int(start_x), int(start_y))
            end_point = (int(end_x), int(end_y))
        elif body["face_position"] == "Right":
            start_y = nose_y + config.face_position_arrow_offset_y
            end_y = nose_y + config.face_position_arrow_offset_y
            start_x = nose_x + (config.face_position_arrow_length / 2) + \
                config.face_position_arrow_offset_x
            end_x = nose_x - (config.face_position_arrow_length / 2) + \
                config.face_position_arrow_offset_x
            start_point = (int(start_x), int(start_y))
            end_point = (int(end_x), int(end_y))
        elif body["face_position"] == "Left":
            start_y = nose_y + config.face_position_arrow_offset_y
            end_y = nose_y + config.face_position_arrow_offset_y
            start_x = nose_x - (config.face_position_arrow_length / 2) + \
                config.face_position_arrow_offset_x
            end_x = nose_x + (config.face_position_arrow_length / 2) + \
                config.face_position_arrow_offset_x
            start_point = (int(start_x), int(start_y))
            end_point = (int(end_x), int(end_y))
        else:
            start_y = nose_y + (config.face_position_arrow_length / 2) + \
                config.face_position_arrow_offset_y
            end_y = nose_y - (config.face_position_arrow_length / 2) + \
                config.face_position_arrow_offset_y
            start_x = nose_x + config.face_position_arrow_offset_x
            end_x = nose_x + config.face_position_arrow_offset_x
            start_point = (int(start_x), int(start_y))
            end_point = (int(end_x), int(end_y))

        cv2.arrowedLine(frame,
                        start_point,
                        end_point,
                        self.__parse_rgb_color(
                            config.face_position_arrow_color),
                        config.face_position_arrow_stroke)
        return frame

    def __draw_forehead_center_dot_on_frame(self, frame, body, config):
        """
        Draw a dot on the frame indicating the forehead center
        """
        if body["has_forehead"] and body["forehead_center"] != (0, 0):
            forehead_x = body["forehead_center"][0]
            forehead_y = body["forehead_center"][1]
            cv2.circle(frame,
                       (forehead_x, forehead_y),
                       config.forehead_center_dot_size,
                       self.__parse_rgb_color(
                           config.forehead_center_dot_color),
                       config.forehead_center_dot_size)

        return frame

    def __draw_body_rectangle_on_frame(self, frame, body, config):
        """
        Draw a rectangle on the frame indicating the body
        """
        if body["has_body"] and body["body_rectangle"] != ((0, 0), (0, 0)):
            upper_left = body["body_rectangle"][0]
            lower_right = body["body_rectangle"][1]
            cv2.rectangle(frame,
                          upper_left,
                          lower_right,
                          self.__parse_rgb_color(config.body_rectangle_color),
                          config.body_rectangle_thickness,
                          lineType=cv2.LINE_AA)

        return frame

    def __draw_landmark_points_on_body(self, frame, body, config):
        """
        Draw the landmark points on the body
        """
        for _, keypoint in body["pose"].keypoints.items():
            if keypoint.score < config.pose_landmark_dot_confidence_threshold:
                continue
            cv2.circle(frame,
                       (int(keypoint.point[0]), int(keypoint.point[1])),
                       config.pose_landmark_dot_size,
                       self.__parse_rgb_color(config.pose_landmark_dot_color),
                       config.pose_landmark_dot_size,
                       lineType=cv2.LINE_AA)

        return frame

    def __find_face_rectangle(self, body, config):
        """
        Find the face rectangle
        """
        face_rectangle = ((0, 0), (0, 0))

        if not body["has_face"]:
            return face_rectangle

        # We have a high enough confidence that the face points are real so let's use them to
        # make a rectangle
        # Find the lowest and highest X and then add a few pixels of padding
        lowest_y = self.__frame_height
        lowest_x = self.__frame_width
        highest_y = 0
        highest_x = 0

        iteration = -1
        for _, keypoint in body["pose"].keypoints.items():
            iteration += 1
            if iteration < 5:
                if int(keypoint.point[0]) < lowest_x:
                    lowest_x = int(keypoint.point[0])
                if int(keypoint.point[1]) < lowest_y:
                    lowest_y = int(keypoint.point[1])
                if int(keypoint.point[0]) > highest_x:
                    highest_x = int(keypoint.point[0])
                if int(keypoint.point[1]) > highest_y:
                    highest_y = int(keypoint.point[1])
            else:
                continue

        # Use face position information to determine how to adjust the X coordinates
        x_spread = highest_x - lowest_x
        y_spread = highest_y - lowest_y
        if y_spread == 0:
            y_spread = 1
        x_factor = 0

        if body["face_position"] == "Straight":
            lowest_x -= 8
            highest_x += 8
            x_factor = x_spread / y_spread * 0.8
        elif body["face_position"] == "Right":
            lowest_x -= 8
            highest_x += (x_spread * 0.75)
            x_factor = x_spread / y_spread * 1.1
        elif body["face_position"] == "Left":
            highest_x += 8
            lowest_x -= (x_spread * 0.75)
            x_factor = x_spread / y_spread * 1.1
        else:
            lowest_x -= 0
            highest_x += 0
            x_factor = x_spread / y_spread * 1.0

        y_expand = y_spread * x_factor * config.face_rectangle_y_factor
        lowest_y -= y_expand
        highest_y += y_expand

        face_rectangle = ((int(lowest_x), int(lowest_y)),
                         (int(highest_x), int(highest_y)))

        return face_rectangle

    def __draw_centroid_circles_on_frame(self, frame, body, config):
        """
        Draw the centroid circles on the frame
        """
        centroid = body["tracking_info"]["centroid"]
        text = f"OBJECT {body['body_id']}"
        cv2.putText(frame,
                    text,
                    (centroid[0] - 10,
                     centroid[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    self.__parse_rgb_color(config.centroid_dots_color),
                    2,
                    cv2.LINE_AA)
        cv2.circle(frame,
                   (centroid[0], centroid[1]),
                   config.centroid_dots_size,
                   self.__parse_rgb_color(config.centroid_dots_color),
                   config.centroid_dots_size,
                   lineType=cv2.LINE_AA)
        return frame

    def __draw_face_rectangle_on_frame(self, frame, body, config):
        """
        Draw the face rectangle on the frame
        """
        if body["has_face"] and body["face_rectangle"] != ((0, 0), (0, 0)):
            upper_left = body["face_rectangle"][0]
            lower_right = body["face_rectangle"][1]
            cv2.rectangle(frame,
                          upper_left,
                          lower_right,
                          self.__parse_rgb_color(config.face_rectangle_color),
                          config.face_rectangle_thickness,
                          lineType=cv2.LINE_AA)
        return frame

    def __parse_rgb_color(self, color_rgb):
        """
        Parse the RGB color
        """
        return (color_rgb.blue(), color_rgb.green(), color_rgb.red())

    def __find_body_rectangle(self, body):
        """
        Find the body rectangle
        """
        body_rectangle = ((0, 0), (0, 0))

        if body["has_body"]:
            # We have a high enough confidence that the body points are real so let's use them to
            # make a rectangle
            # #Find the lowest and highest X and Y and then add a few pixels of padding
            lowest_y = self.__frame_height
            lowest_x = self.__frame_width
            highest_y = 0
            highest_x = 0

            iteration = -1
            for _, keypoint in body["pose"].keypoints.items():
                iteration += 1
                if iteration < 5:
                    continue
                else:
                    if int(keypoint.point[0]) < lowest_x:
                        lowest_x = int(keypoint.point[0])
                    if int(keypoint.point[1]) < lowest_y:
                        lowest_y = int(keypoint.point[1])
                    if int(keypoint.point[0]) > highest_x:
                        highest_x = int(keypoint.point[0])
                    if int(keypoint.point[1]) > highest_y:
                        highest_y = int(keypoint.point[1])

            body_rectangle = ((int(lowest_x - 2), int(lowest_y - 2)),
                             (int(highest_x + 2), int(highest_y + 2)))

        return body_rectangle

    def __determine_if_forehead_visible(self, body):
        """
        Determine if the forehead is visible
        """
        has_forehead = False

        if body["has_face"] and body["face_position"] != "Away":
            has_forehead = True

        return has_forehead

    def __determine_face_position(self, body, config):
        """
        Determine the face position
        """
        # Calculate combo scores of different sets
        pose = body["pose"]
        left_eye_left_ear_score = (
            pose.keypoints[1].score + pose.keypoints[3].score) / 2
        right_eye_right_ear_score = (
            pose.keypoints[2].score + pose.keypoints[4].score) / 2
        eye_and_nose_score = (pose.keypoints[0].score + pose.keypoints[2].score +
                           pose.keypoints[1].score) / 3
        rightness = left_eye_left_ear_score - right_eye_right_ear_score
        leftness = right_eye_right_ear_score - left_eye_left_ear_score

        face_position = "Unknown"

        if body["has_face"]:
            if (-1 * config.face_position_left_right_threshold) < rightness < \
                    config.face_position_left_right_threshold and \
                    (-1 * config.face_position_left_right_threshold) < leftness < \
                    config.face_position_left_right_threshold and \
                    eye_and_nose_score >= config.face_position_straight_threshold:
                face_position = "Straight"
            elif rightness >= config.face_position_left_right_threshold and \
                    leftness <= (-1 * config.face_position_left_right_threshold):
                face_position = "Right"
            elif leftness >= config.face_position_left_right_threshold and \
                    rightness <= (-1 * config.face_position_left_right_threshold):
                face_position = "Left"
            else:
                face_position = "Away"
        else:
            face_position = "Away"

        return face_position

    def __determine_forehead_center(self, body):
        """
        Determine the forehead center
        """
        forehead_center = (0, 0)

        if body["has_forehead"]:
            # Get eye locations
            left_eye_x = int(body["pose"].keypoints[1].point[0])
            left_eye_y = int(body["pose"].keypoints[1].point[1])
            right_eye_x = int(body["pose"].keypoints[2].point[0])
            right_eye_y = int(body["pose"].keypoints[2].point[1])

            # Adjust the eye vertical position by 1 pixel if they are exactly equal so we don't
            # have 0 slope
            d_y = right_eye_y - left_eye_y
            if d_y == 0:
                d_y = 1

            d_x = right_eye_x - left_eye_x
            if d_x == 0:
                d_x = 1

            # Calculate distance between eyes and set distance to forehead
            eye_slope = d_y / d_x
            eye_distance = math.sqrt((d_x * d_x) + (d_y * d_y))
            distance_to_forehead = eye_distance * 0.5
            inverse_eye_slope = -1 / eye_slope
            mid_x = (left_eye_x + right_eye_x) / 2
            mid_y = (left_eye_y + right_eye_y) / 2
            end_constant = distance_to_forehead / \
                math.sqrt(1 + (inverse_eye_slope * inverse_eye_slope))
            forehead_x = 0
            forehead_y = 0

            if eye_slope < 0:
                forehead_x = int(mid_x - end_constant)
                forehead_y = int(mid_y - (end_constant * inverse_eye_slope))
            else:
                forehead_x = int(mid_x + end_constant)
                forehead_y = int(mid_y + (end_constant * inverse_eye_slope))

            forehead_center = (forehead_x, forehead_y)

        return forehead_center

    def __get_euclidean_distance_between_two_points(self, point1, point2, coordinate_count):
        """
        Get the euclidean distance between two points
        """
        tmp_sum = 0

        for i in range(coordinate_count):
            tmp_sum += (point1[i] - point2[i]) ** 2

        distance = tmp_sum ** 0.5
        return distance

    def __add_new_body_to_tracker(self):
        """
        Add a new body to the tracker
        """
        self.__body_number += 1
        self.__body_missing[self.__body_number] = 0
        self.__body_history[self.__body_number] = OrderedDict()
        self.__body_seen[self.__body_number] = OrderedDict()

        return self.__body_number

    def __record_body_seen_value_for_current_frame(self, frame_number, body_id, seen, config):
        self.__body_seen[body_id][frame_number] = seen

        if len(self.__body_seen[body_id]) > config.person_tracking_creation_m:
            self.__body_seen[body_id].popitem(last=False)

    def __determine_if_body_seen_enough_to_create_person(self, body_id, config):
        """
        Determine if the body is seen enough to create a person
        """
        ready_for_creation = False
        # We need to see if the key is present for safety otherwise we could throw a "key error"
        if body_id in self.__body_seen:
            # Shortcut processing by looking if we can possibly have enough "seen" occurrences yet
            if len(self.__body_seen[body_id]) >= config.person_tracking_creation_n:
                yes_count = 0

                for _, was_seen in self.__body_seen[body_id].items():
                    if was_seen:
                        yes_count += 1

                if yes_count >= config.person_tracking_creation_n:
                    ready_for_creation = True

        return ready_for_creation

    def __record_body_info_in_tracker_for_id(self, frame_number, body_id, body_info, config):
        """
        Record body info in the tracker for the given id
        """
        self.__body_missing[body_id] = 0
        self.__body_history[body_id][frame_number] = body_info
        self.__record_body_seen_value_for_current_frame(
            frame_number, body_id, True, config)

        if len(self.__body_history[body_id]) > config.object_tracking_info_history_count:
            self.__body_history[body_id].popitem(last=False)

    def __process_cleanup_of_missing_bodies(self, config):
        """
        Cleanup of missing bodies
        """
        # Loop through the entries for missing bodies and find any that have been missing too long
        for body_id in list(self.__body_missing.keys()):
            if self.__body_missing[body_id] > config.object_tracking_removal_count and \
                    body_id in self.__person_data:
                person_data = self.__person_data[body_id]
                person_id = person_data["uuid"]

                # EMIT PERSON GONE EVENT
                self.emit("person_left_scene", person_id)

                del self.__body_missing[body_id]
                del self.__body_history[body_id]
                del self.__body_seen[body_id]
                del self.__person_data[body_id]

    def __mark_unmatched_body_ids_as_missing(self, current_frame_number, config):
        """
        Mark unmatched body ids as missing
        """
        # Loop through the body history and see if any do not have matches for the current frame
        for body_id in list(self.__body_history.keys()):
            if current_frame_number in self.__body_history[body_id]:
                continue
            else:
                self.__body_missing[body_id] += 1
                self.__record_body_seen_value_for_current_frame(current_frame_number,
                                                                body_id,
                                                                False,
                                                                config)

    def __check_if_person_data_record_exists_for_body_id(self, body_id):
        """
        Check if a person data record exists for the given body id
        """
        return bool(body_id in self.__person_data)

    def __create_new_person_data_record_with_body_id(self, body_id):
        """
        Create a new person data record with the given body id
        """
        # Use UUID version 4 (full random) and just take the first 8 characters
        person_uuid = str(uuid.uuid4())[0:8]

        # Create standard dictionary for storing person data with default values
        # The detection history fields are ordered dictionary objects because we will need to pop
        # old readings off the list
        data = {}
        data["uuid"] = person_uuid
        data["is_poi"] = False

        self.__person_data[body_id] = data

        # EMIT NEW PERSON EVENT
        self.emit("new_person_entered_scene", person_uuid)

    def __generate_tracking_info_for_body(self, frame, body, config):
        """
        Generate tracking info for the given body
        """
        tracking_info = {}
        centroid = (0, 0)
        size = (0, 0)
        average_color = (0, 0, 0)

        start_x = 0
        start_y = 0
        end_x = 0
        end_y = 0

        if body["has_face"]:
            start_x = body["face_rectangle"][0][0]
            start_y = body["face_rectangle"][0][1]
            end_x = body["face_rectangle"][1][0]
            end_y = body["face_rectangle"][1][1]
        else:
            start_x = body["body_rectangle"][0][0]
            start_y = body["body_rectangle"][0][1]
            end_x = body["body_rectangle"][1][0]
            end_y = body["body_rectangle"][1][1]

        size_w = int(end_x - start_x)
        size_h = int(end_y - start_y)
        centroid_x = int((start_x + end_x) / 2)
        centroid_y = int((start_y + end_y) / 2)

        size = (size_w, size_h)
        centroid = (centroid_x, centroid_y)

        centroid_color_sample_start_x = \
            max(centroid_x - int(config.object_tracking_color_sample_pixels / 2), 0)
        centroid_color_sample_end_x = \
            min(centroid_x + int(config.object_tracking_color_sample_pixels / 2),
                self.__frame_width)
        centroid_color_sample_start_y = \
            max(centroid_y - int(config.object_tracking_color_sample_pixels / 2), 0)
        centroid_color_sample_end_y = \
            min(centroid_y + int(config.object_tracking_color_sample_pixels / 2),
                self.__frame_height)

        centroid_color_sample_start_x = min(
            centroid_color_sample_start_x, (self.__frame_width - 1))
        centroid_color_sample_end_x = max(centroid_color_sample_end_x, 1)
        centroid_color_sample_start_y = min(
            centroid_color_sample_start_y, (self.__frame_height - 1))
        centroid_color_sample_end_y = max(centroid_color_sample_end_y, 1)

        color_sample_chunk = frame[centroid_color_sample_start_y: centroid_color_sample_end_y,
                                 centroid_color_sample_start_x: centroid_color_sample_end_x]

        # Find the average pixel color values for BGR
        avg_blue = 0
        avg_green = 0
        avg_red = 0

        avg_color_per_row = np.average(color_sample_chunk, axis=0)
        avg_color = np.average(avg_color_per_row, axis=0)
        avg_blue = int(avg_color[0])
        avg_green = int(avg_color[1])
        avg_red = int(avg_color[2])

        average_color = (avg_blue, avg_green, avg_red)

        tracking_info["size"] = size
        tracking_info["centroid"] = centroid
        tracking_info["color"] = average_color

        return tracking_info

    def __apply_best_object_matches_to_body_tracking_info(self,
                                                          current_frame_number,
                                                          bodies,
                                                          config):
        """
        Apply best object matches to body tracking info
        """
        for body in bodies:
            tracking_info = body["tracking_info"]
            score_list = OrderedDict()
            lowest_score = 1000

            # Loop through existing body ID histories and compute matching
            for existing_body_id in list(self.__body_history.keys()):
                # Loop through the history - keys will be frame numbers - and throw out history
                # entries that are too old
                # List will be oldest entries first
                history_num = 0
                vector_x = 0
                vector_y = 0
                prior_x = 0
                prior_y = 0
                cum_centroid_distance = 0
                cum_color_distance = 0
                cum_size_distance = 0
                cum_centroid_with_vector_distance = 0

                for history_frame_number in list(self.__body_history[existing_body_id].keys()):
                    # This history entry is valid - proceed
                    history_num += 1

                    # First add to the vector if we are not on the first history frame
                    if history_num > 1:
                        vector_x += (self.__body_history[existing_body_id]
                                    [history_frame_number]["centroid"][0] - prior_x)
                        vector_y += (self.__body_history[existing_body_id]
                                    [history_frame_number]["centroid"][1] - prior_y)

                    prior_x = \
                        self.__body_history[existing_body_id][history_frame_number]["centroid"][0]
                    prior_y = \
                        self.__body_history[existing_body_id][history_frame_number]["centroid"][1]

                    cum_centroid_distance += self.__get_euclidean_distance_between_two_points(
                        self.__body_history[existing_body_id][history_frame_number]["centroid"],
                        tracking_info["centroid"],
                        2)
                    cum_color_distance += self.__get_euclidean_distance_between_two_points(
                        self.__body_history[existing_body_id][history_frame_number]["color"],
                        tracking_info["color"],
                        3)
                    cum_size_distance += self.__get_euclidean_distance_between_two_points(
                        self.__body_history[existing_body_id][history_frame_number]["size"],
                        tracking_info["size"],
                        2)

                if history_num > 1:
                    vector_x = vector_x / (history_num - 1)
                    vector_y = vector_y / (history_num - 1)

                projected_x = prior_x + vector_x
                projected_y = prior_y + vector_y

                cum_centroid_with_vector_distance = \
                    self.__get_euclidean_distance_between_two_points((projected_x, projected_y),
                                                                      tracking_info["centroid"],
                                                                      2)

                cum_centroid_distance = cum_centroid_distance / history_num
                cum_color_distance = cum_color_distance / history_num
                cum_size_distance = cum_size_distance / history_num

                total_current_score = \
                    (config.object_tracking_centroid_weight * cum_centroid_distance) + \
                    (config.object_tracking_color_weight * cum_color_distance) + \
                    (config.object_tracking_vector_weight * cum_centroid_with_vector_distance) + \
                    (config.object_tracking_size_weight * cum_size_distance)
                score_list[existing_body_id] = total_current_score
                if total_current_score < lowest_score:
                    lowest_score = total_current_score

            body["score_list"] = score_list
            body["lowest_score"] = lowest_score

        # Loop through the objects and find the lowest score that is also the lowest score for
        # that body
        for existing_body_id in list(self.__body_history.keys()):
            obj_lowest_score = 1000
            obj_best_body_iterator = -1
            body_iter = -1

            for body in bodies:
                body_iter += 1
                this_obj_score = body["score_list"][existing_body_id]

                if this_obj_score < obj_lowest_score and body["lowest_score"] == this_obj_score:
                    obj_lowest_score = this_obj_score
                    obj_best_body_iterator = body_iter

            if obj_best_body_iterator > -1:
                self.__record_body_info_in_tracker_for_id(
                    current_frame_number,
                    existing_body_id,
                    bodies[obj_best_body_iterator]["tracking_info"],
                    config)
                bodies[obj_best_body_iterator]["body_id"] = existing_body_id

                # Check if we have a person data record yet
                has_person = self.__check_if_person_data_record_exists_for_body_id(
                    existing_body_id)

                if has_person:
                    # Add the person ID to the body
                    bodies[obj_best_body_iterator]["person_id"] = existing_body_id
                else:
                    # See if we can create one based on our appearance history
                    _ = self.__determine_if_body_seen_enough_to_create_person(
                        existing_body_id, config)
                    self.__create_new_person_data_record_with_body_id(existing_body_id)
                    bodies[obj_best_body_iterator]["person_id"] = existing_body_id

        # Loop through bodies one last time to see if any do not have an object ID yet
        for body in bodies:
            if body["body_id"] == 0:
                new_object_id = self.__add_new_body_to_tracker()
                body["body_id"] = new_object_id
                self.__body_history[new_object_id][current_frame_number] = body["tracking_info"]
                self.__body_missing[new_object_id] = 0

    def __set_person_as_poi(self, person_id):
        """
        Sets the person as a POI
        """
        self.__prior_poi_id = person_id

        for cur_person_id in self.__person_data:
            if cur_person_id == person_id:
                self.__person_data[person_id]["is_poi"] = True
            else:
                self.__person_data[person_id]["is_poi"] = False

        # EMIT NEW POI EVENT
        person_uuid = self.__person_data[person_id]["uuid"]
        self.emit("new_person_in_front", person_uuid)

    def __draw_person_data_on_frame(self, frame, body, config):
        """
        Draws the person data on the frame
        """
        if not body["person_id"] in self.__person_data:
            return frame

        # Get data to display
        person_id_value = self.__person_data[body["person_id"]]["uuid"]

        # Assemble output text strings
        identity_text = f"{config.identity_text_prefix}{person_id_value}"

        # Calculate total height from which lines of text are being shown
        id_height = 0
        id_base_line = 0

        if config.show_person_id:
            (_, id_height), id_base_line = cv2.getTextSize(
                identity_text,
                cv2.FONT_HERSHEY_SIMPLEX,
                config.person_data_identity_text_font_size,
                config.person_data_identity_text_stroke)

        # Add line and baseline heights together to find the total height
        total_text_height_with_baselines = int(id_height + id_base_line)
        half_height = int(total_text_height_with_baselines / 2)

        # Get forehead X,Y position for this body
        forehead_center = body["forehead_center"]

        # Determine end coordinates for data line
        line_end_x = forehead_center[0] + config.person_data_text_offset_x
        line_end_y = 0
        text_start_y = 0

        if config.person_data_text_offset_y <= 0:
            line_end_y = forehead_center[1] + \
                config.person_data_text_offset_y - half_height
            text_start_y = forehead_center[1] + \
                config.person_data_text_offset_y - total_text_height_with_baselines
        else:
            line_end_y = forehead_center[1] + \
                config.person_data_text_offset_y + half_height
            text_start_y = forehead_center[1] + config.person_data_text_offset_y

        # Draw line from forehead center to person data text box
        cv2.line(frame, forehead_center, (line_end_x, line_end_y), self.__parse_rgb_color(
            config.person_data_line_color),
            config.person_data_line_thickness,
            lineType=cv2.LINE_AA)

        if config.show_person_id:
            id_write_y = text_start_y + id_height + id_base_line
            cv2.putText(frame, identity_text, (line_end_x, id_write_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        config.person_data_identity_text_font_size,
                        self.__parse_rgb_color(config.person_data_identity_text_color),
                        config.person_data_identity_text_stroke,
                        cv2.LINE_AA)

        return frame
