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

# pylint: skip-file
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

Point = collections.namedtuple('Point', ['x', 'y'])
Point.distance = lambda a, b: math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)
Point.distance = staticmethod(Point.distance)

Keypoint = collections.namedtuple('Keypoint', ['point', 'score'])

Pose = collections.namedtuple('Pose', ['keypoints', 'score'])

class PoseEngine():
    """Engine used for pose tasks."""
    __POSENET_SHARED_LIB = {
        'Linux': 'posenet_decoder.so',
        'Darwin': 'posenet_decoder.so',
        'Windows': 'posenet_decoder.dll'
        }[platform.system()]

    def __init__(self,
                 model_path,
                 mirror=False,
                 arch=platform.uname().machine,
                 tpu:bool=True,
                 num_cpu_threads:int=1,
                 minimum_pose_threshold:float=0.2):
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

        self.__is_windows = platform.system() == "Windows"

        script_dir = os.path.dirname(os.path.realpath(__file__))

        if importlib.util.find_spec("tflite_runtime") is not None:
            tf = import_module("tflite_runtime.interpreter")
            load_delegate = tf.load_delegate
            Interpreter = tf.Interpreter
        else:
            tf = import_module("tensorflow")
            load_delegate = tf.lite.experimental.load_delegate
            Interpreter = tf.lite.Interpreter

        if self.__is_windows:
            model_path = os.path.join(script_dir, "cpu", "models", "movenet_multipose.tflite")
            self._interpreter = Interpreter(model_path, num_threads=num_cpu_threads)
            self._interpreter.allocate_tensors()
        else:
            sysname = platform.uname().system.lower()
            posenet_shared_lib = os.path.join(
                script_dir, "posenet_lib", arch, sysname, PoseEngine.__POSENET_SHARED_LIB)

            if not os.path.exists(posenet_shared_lib):
                raise ValueError("Posenet library not found at %s" % posenet_shared_lib)

            posenet_decoder_delegate = load_delegate(posenet_shared_lib)
            delegates = [posenet_decoder_delegate]

            if tpu:
                self.__edgetpu = import_module("pycoral.utils.edgetpu")
                edgetpu_delegate = load_delegate(Perceptor.EDGETPU_SHARED_LIB)
                delegates.append(edgetpu_delegate)

            self._interpreter = Interpreter(
                model_path, experimental_delegates=delegates, num_threads=num_cpu_threads)
            self._interpreter.allocate_tensors()

        self._mirror = mirror

        self._input_tensor_shape = self.get_input_tensor_shape()
        if (self._input_tensor_shape.size != 4 or
                self._input_tensor_shape[3] != 3 or
                self._input_tensor_shape[0] != 1):
            raise ValueError(
                ("Image model should have input shape [1, height, width, 3]!"
                 " This model has {}.".format(self._input_tensor_shape)))
        _, self._input_height, self._input_width, self._input_depth = self.get_input_tensor_shape()
        self._input_type = self._interpreter.get_input_details()[0]['dtype']
        self._input_details = self._interpreter.get_input_details()
        self._output_details = self._interpreter.get_output_details()
        self._inf_time = 0
        self.__tpu = tpu and not self.__is_windows
        self.__minimum_pose_threshold = minimum_pose_threshold

    def run_inference(self, input_data):
        """
        Run inference using the zero copy feature from pycoral and returns inference time in ms.
        """
        start = time.monotonic()
        if not self.__tpu:
            self._interpreter.set_tensor(self._interpreter.get_input_details()[0]['index'], input_data)
            self._interpreter.invoke()
        else:
            self.__edgetpu.run_inference(self._interpreter, input_data)
        self._inf_time = time.monotonic() - start
        return (self._inf_time * 1000)

    def DetectPosesInImage(self, input_image):
        """
        Detects poses in a given image.
        For ideal results make sure the image fed to this function is close to the
        expected input size - it is the caller's responsibility to resize the
        image accordingly.

        # Arguments
        img: numpy array containing image
        """
        if self.__is_windows:
            return self.DetectPosesInImageWindows(input_image)

        # Extend or crop the input to match the input shape of the network.
        if input_image.shape[0] < self._input_height or input_image.shape[1] < self._input_width:
            input_image = np.pad(input_image, [[0, max(0, self._input_height - input_image.shape[0])],
                               [0, max(0, self._input_width - input_image.shape[1])], [0, 0]],
                         mode='constant')
        input_image = input_image[0:self._input_height, 0:self._input_width]
        assert (input_image.shape == tuple(self._input_tensor_shape[1:]))

        input_data = np.expand_dims(input_image, axis=0)
        if self._input_type is np.float32:
            # Floating point versions of posenet take image data in [-1,1] range.
            input_data = np.float32(input_image) / 128.0 - 1.0
        else:
            # Assuming to be uint8
            input_data = np.asarray(input_image)

        if not self.__tpu:
            input_data = np.expand_dims(input_data, axis=0)
        else:
            input_data = input_data.flatten()
    
        self.run_inference(input_data)
    
        return self.ParseOutput()

    def DetectPosesInImageWindows(self, input_image):
        """
        Detects poses in a given image.
        For ideal results make sure the image fed to this function is close to the
        expected input size - it is the caller's responsibility to resize the
        image accordingly.

        # Arguments
        img: numpy array containing image
        """
        if not self.__is_windows:
            return self.DetectPosesInImage(input_image)

        is_dynamic_shape_model = self._input_details[0]['shape_signature'][2] == -1
        # Resize and pad the image to keep the aspect ratio and fit the expected
        # size.
        if is_dynamic_shape_model:
            resized_image, _ = self.__keep_aspect_ratio_resizer(
                input_image, 256)
            input_tensor = np.expand_dims(resized_image, axis=0)
            self._interpreter.resize_tensor_input(
                self._input_details[0]['index'], input_tensor.shape, strict=True)
        else:
            resized_image = cv2.resize(input_image,
                                        (self._input_width, self._input_height))
            input_tensor = np.expand_dims(resized_image, axis=0)
        self._interpreter.allocate_tensors()

        # Run inference with the MoveNet MultiPose model.
        self._interpreter.set_tensor(self._input_details[0]['index'],
                                    input_tensor.astype(self._input_type))
        self._interpreter.invoke()

        # Get the model output
        model_output = self._interpreter.get_tensor(
            self._output_details[0]['index'])

        image_height, image_width, _ = input_image.shape
    
        return self.ParseOutputWindows(model_output, image_height, image_width)

    def get_input_tensor_shape(self):
        """Returns input tensor shape."""
        return self._interpreter.get_input_details()[0]['shape']

    def get_output_tensor(self, idx):
        """Returns output tensor view."""
        return np.squeeze(self._interpreter.tensor(
            self._interpreter.get_output_details()[idx]['index'])())

    def ParseOutput(self):
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

    def ParseOutputWindows(self, keypoints_with_scores, image_height, image_width):
        """Parses interpreter output tensors and returns decoded poses."""
        _, num_instances, _ = keypoints_with_scores.shape
        poses = []

        for idx in range(num_instances):
            pose_score = keypoints_with_scores[0, idx, 55]
            if pose_score < 0.3: # self.__minimum_pose_threshold:
                continue

            kpts_y = keypoints_with_scores[0, idx, range(0, 51, 3)]
            kpts_x = keypoints_with_scores[0, idx, range(1, 51, 3)]
            scores = keypoints_with_scores[0, idx, range(2, 51, 3)]
    
            pose_keypoints = {}
            for i in range(scores.shape[0]):
                x = int(kpts_x[i] * image_width)
                y = int(kpts_y[i] * image_height)
                pose_keypoints[KeypointType(i)] = Keypoint(
                    Point(x, y), scores[i])
            poses.append(Pose(pose_keypoints, pose_score))

        return poses, self._inf_time

    def __keep_aspect_ratio_resizer(self, image, target_size):
        """Resizes the image.
        The function resizes the image such that its longer side matches the required
        target_size while keeping the image aspect ratio. Note that the resizes image
        is padded such that both height and width are a multiple of 32, which is
        required by the model. See
        https://tfhub.dev/google/tfjs-model/movenet/multipose/lightning/1 for more
        detail.
        Args:
            image: The input RGB image as a numpy array of shape [height, width, 3].
            target_size: Desired size that the image should be resize to.
        Returns:
            image: The resized image.
            (target_height, target_width): The actual image size after resize.
        """
        height, width, _ = image.shape
        if height > width:
            scale = float(target_size / height)
            target_height = target_size
            scaled_width = math.ceil(width * scale)
            image = cv2.resize(image, (scaled_width, target_height))
            target_width = int(math.ceil(scaled_width / 32) * 32)
        else:
            scale = float(target_size / width)
            target_width = target_size
            scaled_height = math.ceil(height * scale)
            image = cv2.resize(image, (target_width, scaled_height))
            target_height = int(math.ceil(scaled_height / 32) * 32)

        padding_top, padding_left = 0, 0
        padding_bottom = target_height - image.shape[0]
        padding_right = target_width - image.shape[1]
        # add padding to image
        image = cv2.copyMakeBorder(image, padding_top, padding_bottom, padding_left,
                                    padding_right, cv2.BORDER_CONSTANT)
        return image, (target_height, target_width)


class PeoplePerceptorBase(Perceptor):
    def __init__(self):
        super().__init__(model_path="")

        self.set_config_schema([
            Config("minimum_face_threshold", "Minimum Face Threshold", "float", 0.4, "Confidence threshold for detecting the face as a percent certainty"),
            Config("minimum_body_threshold", "Minimum Body Threshold", "float", 0.2, "Confidence threshold for detecting the body as a percent certainty"),
            Config("minimum_face_height", "Minimum Face Height", "int", 20, "The minimum height of the persons face in pixels that we want to work with"),
            Config("minimum_body_height", "Minimum Body Height", "int", 120, "The minimum height of the persons body in pixels that we want to work with"),
            Config("show_pose_landmark_dots", "Show pose landmark dots", "bool", False, "Show pose landmark dots (nose, ears, elbows, etc.)"),
            Config("show_body_rectangle", "Show body rectangle", "bool", False, "Draw a rectangle around the persons body"),
            Config("show_face_rectangle", "Show face rectangle", "bool", False, "Draw a rectangle around the persons face"),
            Config("face_rectangle_color", "Face rectangle color", "rgb", RGB(255, 0, 0), "Color of the face rectangle"),
            Config("face_rectangle_thickness", "Face rectangle thickness", "int", 1, "Thickness of the face rectangle"),
            Config("body_rectangle_color", "Body rectangle color", "rgb", RGB(0, 255, 0), "Color of the body rectangle"),
            Config("body_rectangle_thickness", "Body rectangle thickness", "int", 1, "Thickness of the body rectangle"),
            Config("pose_landmark_dot_confidence_threshold", "Pose landmark dot confidence threshold", "float", 0.5, "Confidence threshold for identifying pose landmarks as a percent certainty"),
            Config("pose_landmark_dot_size", "Pose landmark dot size", "int", 1, "Size of the pose landmark dots"),
            Config("pose_landmark_dot_color", "Pose landmark dot color", "rgb", RGB(255, 255, 255), "Color of the pose landmark dots"),
            Config("show_face_position_arrow", "Show face position arrow", "bool", False, "Show the arrow that indicates which direction the person is looking"),
            Config("face_position_arrow_color", "Face position arrow color", "rgb", RGB(255, 255, 255), "Color of the face position arrow"),
            Config("face_position_arrow_stroke", "Face position arrow stroke", "int", 1, "Thickness of the face position arrow"),
            Config("face_position_arrow_offset_x", "Face position arrow offset x", "int", 0, "X offset for the face position arrow"),
            Config("face_position_arrow_offset_y", "Face position arrow offset y", "int", -30, "Y offset for the face position arrow"),
            Config("face_position_arrow_length", "Face position arrow length", "int", 20, "Length of the face position arrow"),
            Config("face_position_left_right_threshold", "Face position left/right threshold", "float", 0.3, "Threshold for detecting if the person is looking left or right"),
            Config("face_position_straight_threshold", "Face position straight threshold", "float", 0.7, "Threshold for detecting if the person is looking straight"),
            Config("show_forehead_center_dot", "Show forehead center dot", "bool", False, "Show a dot in the center of the persons forehead"),
            Config("forehead_center_dot_color", "Forehead center dot color", "rgb", RGB(255, 255, 255), "Color of the forehead center dot"),
            Config("forehead_center_dot_size", "Forehead center dot size", "int", 1, "Size of the forehead center dot"),
            Config("face_rectangle_y_factor", "Face rectangle Y factor", "float", 1.0, "Size adjustment factor for the height of the persons face, which can be used to make sure objects like hair and hats are captured"),
            Config("show_centroid_dots", "Show centroid information", "bool", False, "Show centroid information (center of the face or body)"),
            Config("centroid_dots_color", "Centroid information color", "rgb", RGB(255, 255, 255), "Color of the centroid information"),
            Config("centroid_dots_size", "Centroid information size", "int", 1, "Size of the centroid information"),
            Config("object_tracking_allowed_missed_frames", "Object tracking allowed missed frames", "int", 50, "Object tracking allowed missed frames"),
            Config("object_tracking_color_sample_pixels", "Object tracking color sample pixels", "int", 4, "Number of pixels to use for color sampling when tracking objects"),
            Config("object_tracking_info_history_count", "Object tracking info history count", "int", 3, "Number of video frames used to track an object in the field of view"),
            Config("object_tracking_removal_count", "Object tracking removal count", "int", 50, "Number of frames to wait before removing an object from tracking"),
            Config("object_tracking_centroid_weight", "Object tracking centroid weight", "float", 0.25, "Level of importance that centroid data has when tracking objects"),
            Config("object_tracking_color_weight", "Object tracking color weight", "float", 0.25, "Level of importance that color data has when tracking objects"),
            Config("object_tracking_vector_weight", "Object tracking vector weight", "float", 0.25, "Level of importance that vector data has when tracking objects"),
            Config("object_tracking_size_weight", "Object tracking size weight", "float", 0.25, "Level of importance that size data has when tracking objects"),
            Config("object_tracking_creation_m", "Object tracking creation M", "int", 10, "Minimum number of frames out of N frames that an object must be present in the field of view before it is tracked"),
            Config("object_tracking_creation_n", "Object tracking creation N", "int", 7, "Total number of frames used to evaluate an object before it is tracked"),
            Config("person_tracking_creation_m", "Person tracking creation M", "int", 20, "Minimum number of frames out of N frames needed to promote a tracked object to a person"),
            Config("person_tracking_creation_n", "Person tracking creation N", "int", 16, "Total number of frames used to evaluate a tracked object before it is promoted to a person"),
            Config("show_person_id", "Show person ID", "bool", False, "Show anonymous unique identifier for the person"),
            Config("person_data_line_color", "Person data line color", "rgb", RGB(255, 255, 255), "Color of the person data line"),
            Config("person_data_line_thickness", "Person data line thickness", "int", 1, "Thickness of the person data line"),
            Config("person_data_identity_text_color", "Person data identity text color", "rgb", RGB(255, 255, 255), "Color of the person data identity text"),
            Config("person_data_identity_text_stroke", "Person data identity text stroke", "int", 1, "Thickness of the person data identity text"),
            Config("person_data_identity_text_font_size", "Person data identity text font size", "float", 1.0, "Font size of the person data identity text"),
            Config("person_data_text_offset_x", "Person data text offset X", "int", 30, "X offset of the person data text"),
            Config("person_data_text_offset_y", "Person data text offset Y", "int", -40, "Y offset of the person data text"),
            Config("identity_text_prefix", "Identity text prefix", "str", "Person ID: ", "Text information that you want to display at the beginning of the person ID"),
            Config("rolling_video_storage_frame_count", "Rolling video storage frame count", "int", 100, "Number of the video frames to store while processing"),
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
        if input_data is None:
            return None

        #Start with basic frame operations
        frame = input_data
        self.__frame_number += 1
        self.__set_frame_dimensions(frame)
        self.__add_current_frame_to_rolling_history(frame, config)
        
        #Perform posenet primary AI inference
        poses, _ = primary_pose_engine.DetectPosesInImage(frame)
        
        #Create POM object
        pom = PeoplePOM()

        #Place raw frame into POM
        pom.set_raw_frame(frame.copy())

        #Pass detected poses through body qualifier
        bodies = self.__get_qualified_body_detections(poses, config)

        #Process the bodies for various attributes
        bodies = self.__process_body_attributes(bodies, frame, config)

        #Perform tracking on bodies
        self.__apply_best_object_matches_to_body_tracking_info(self.__frame_number, bodies, config)
        self.__mark_unmatched_body_ids_as_missing(self.__frame_number, config)

        #Check if a new POI has been determined
        if self.__poi != None and ('person_id' in self.__poi) and self.__poi['person_id'] != 0:
            if self.__prior_poi_id != self.__poi['person_id']:
                self.__set_person_as_poi(self.__poi['person_id'], self.__frame_number, self.__poi, config)

        #Perform cleanup on people who are not detected
        self.__process_cleanup_of_missing_bodies(frame, config)

        #Annotate the frame as determined by configuration
        annotated_frame = self.__annotate_frame(bodies, frame.copy(), config)
        pom.set_annotated_frame(annotated_frame)

        people = OrderedDict()
        for body in bodies:
            if self.__check_if_person_data_record_exists_for_body_id(body["body_id"]):
                personIdValue = self.__person_data[body["person_id"]]["uuid"]
                body["person_uuid"] = personIdValue
                body["is_poi"] = self.__person_data[body["person_id"]]["is_poi"]
                people[personIdValue] = body
        pom.set_people(people)
        return pom

    def __set_frame_dimensions(self, frame):
        self.__frame_width = frame.shape[1]
        self.__frame_height = frame.shape[0]

    def __add_current_frame_to_rolling_history(self, frame, config):
        milltime = int(round(time.time() * 1000))
        curFrame = {"timestamp" : milltime, "frame" : frame.copy()}
        self.__frame_history[self.__frame_number] = curFrame
        
        if len(self.__frame_history) > config.rolling_video_storage_frame_count:
            self.__frame_history.popitem(last=False)

    def __process_body_attributes(self, bodies, frame, config):
        max_face_height = 0
        body_with_max_face_height = None
        for body in bodies:
            body["face_position"] = self.__determine_face_position(body, config)
            body["has_forehead"] = self.__determine_if_forehead_visible(body, config)
            body["forehead_center"] = self.__determine_forehead_center(body, config)
            body["body_rectangle"] = self.__find_body_rectangle(body, config)
            body["face_rectangle"] = self.__find_face_rectangle(body, config)
            body["tracking_info"] = self.__generate_tracking_info_for_body(frame, body, config)

            if not body["has_face"]:
                continue

            curFaceHeight = int(body["face_rectangle"][1][1] - body["face_rectangle"][0][1])
            if curFaceHeight > max_face_height:
                max_face_height = curFaceHeight
                body_with_max_face_height = body

        self.__poi = body_with_max_face_height

        return bodies

    def __annotate_frame(self, bodies, frame, config):
        if config.show_pose_landmark_dots:
            for body in bodies:
                frame = self.__draw_landmark_points_on_body(frame, body, config)

        if config.show_face_position_arrow:
            for body in bodies:
                frame = self.__draw_face_position_arrow_on_frame(frame, body, config)

        if config.show_forehead_center_dot:
            for body in bodies:
                frame = self.__draw_forehead_center_dot_on_frame(frame, body, config)

        if config.show_body_rectangle:
            for body in bodies:
                frame = self.__draw_body_rectangle_on_frame(frame, body, config)
        
        if config.show_face_rectangle:
            for body in bodies:
                frame = self.__draw_face_rectangle_on_frame(frame, body, config)

        if config.show_centroid_dots:
            for body in bodies:
                frame = self.__draw_centroid_circles_on_frame(frame, body, config)

        if config.show_person_id:
            for body in bodies:
                frame = self.__draw_person_data_on_frame(frame, body, config)

        return frame

    def __get_qualified_body_detections(self, poses, config):
        bodies = []
        
        for pose in poses:
            curBody = {}
            meetsConfidence = False
            meetsSize = False
            curBody["person_id"] = 0
            curBody["has_face"] = False
            curBody["has_body"] = False
            curBody["has_forehead"] = False
            curBody["face_score"] = 0.0
            curBody["body_score"] = 0.0
            curBody["body_rectangle"] = ((0,0),(0,0))
            curBody["face_rectangle"] = ((0,0),(0,0))
            curBody["body_id"] = 0
        
            #Compute the confidence scores for face and body separately
            faceScore = (pose.keypoints[0].score + pose.keypoints[1].score + pose.keypoints[2].score + pose.keypoints[3].score + pose.keypoints[4].score) / 5
            bodyScore = (pose.keypoints[5].score + pose.keypoints[6].score + pose.keypoints[7].score + pose.keypoints[8].score + pose.keypoints[9].score + pose.keypoints[10].score + pose.keypoints[11].score + pose.keypoints[12].score + pose.keypoints[13].score + pose.keypoints[14].score + pose.keypoints[15].score + pose.keypoints[16].score) / 12
            
            #Evaluate confidence levels first
            if faceScore >= config.minimum_face_threshold:
                meetsConfidence = True
                curBody["has_face"] = True
                curBody["face_score"] = faceScore
                
            if bodyScore >= config.minimum_body_threshold:
                meetsConfidence = True
                curBody["has_body"] = True
                curBody["body_score"] = bodyScore
                
            #Now check for size requirements
            if meetsConfidence:
                #Get face and body sizes from keypoint coordinates in rough estimate style
                faceHeight = ((pose.keypoints[5].point[1] + pose.keypoints[6].point[1]) / 2) - ((pose.keypoints[1].point[1] + pose.keypoints[2].point[1]) / 2)
                bodyHeight = ((pose.keypoints[15].point[1] + pose.keypoints[16].point[1]) / 2) - pose.keypoints[0].point[1]
                
                if faceHeight >= config.minimum_face_height:
                    meetsSize = True
                    curBody["simple_face_height"] = faceHeight
                
                if bodyHeight >= config.minimum_body_height:
                    meetsSize = True
                    curBody["simple_body_height"] = bodyHeight
                    
                #If we meet both size and confidence requirements, put this body in the output set
                if meetsSize:
                    curBody["pose"] = pose
                    bodies.append(curBody)
        
        return bodies

    def __draw_face_position_arrow_on_frame(self, frame, body, config):
        noseX = body["pose"].keypoints[0].point[0]
        noseY = body["pose"].keypoints[0].point[1]

        start_point = (0,0)
        end_point = (0,0)

        if body["face_position"] == "Straight":
            startY = noseY - (config.face_position_arrow_length / 2) + config.face_position_arrow_offset_y
            endY = noseY + (config.face_position_arrow_length / 2) + config.face_position_arrow_offset_y
            startX = noseX + config.face_position_arrow_offset_x
            endX = noseX + config.face_position_arrow_offset_x
            start_point = (int(startX), int(startY))
            end_point = (int(endX), int(endY))
        elif body["face_position"] == "Right":
            startY = noseY + config.face_position_arrow_offset_y
            endY = noseY + config.face_position_arrow_offset_y
            startX = noseX + (config.face_position_arrow_length / 2) + config.face_position_arrow_offset_x
            endX = noseX - (config.face_position_arrow_length / 2) + config.face_position_arrow_offset_x
            start_point = (int(startX), int(startY))
            end_point = (int(endX), int(endY))
        elif body["face_position"] == "Left":
            startY = noseY + config.face_position_arrow_offset_y
            endY = noseY + config.face_position_arrow_offset_y
            startX = noseX - (config.face_position_arrow_length / 2) + config.face_position_arrow_offset_x
            endX = noseX + (config.face_position_arrow_length / 2) + config.face_position_arrow_offset_x
            start_point = (int(startX), int(startY))
            end_point = (int(endX), int(endY))
        else:
            startY = noseY + (config.face_position_arrow_length / 2) + config.face_position_arrow_offset_y
            endY = noseY - (config.face_position_arrow_length / 2) + config.face_position_arrow_offset_y
            startX = noseX + config.face_position_arrow_offset_x
            endX = noseX + config.face_position_arrow_offset_x
            start_point = (int(startX), int(startY))
            end_point = (int(endX), int(endY))

        cv2.arrowedLine(frame, start_point, end_point, self.__parse_rgb_color(config.face_position_arrow_color), config.face_position_arrow_stroke)
        return frame

    def __draw_forehead_center_dot_on_frame(self, frame, body, config):
        if body["has_forehead"] and body["forehead_center"] != (0,0):
            foreheadX = body["forehead_center"][0]
            foreheadY = body["forehead_center"][1]
            cv2.circle(frame, (foreheadX, foreheadY), config.forehead_center_dot_size, self.__parse_rgb_color(config.forehead_center_dot_color), config.forehead_center_dot_size)

        return frame

    def __draw_body_rectangle_on_frame(self, frame, body, config):
        if body["has_body"] and body["body_rectangle"] != ((0,0),(0,0)):
            upperLeft = body["body_rectangle"][0]
            lowerRight = body["body_rectangle"][1]
            cv2.rectangle(frame, upperLeft, lowerRight, self.__parse_rgb_color(config.body_rectangle_color), config.body_rectangle_thickness, lineType=cv2.LINE_AA)

        return frame

    def __draw_landmark_points_on_body(self, frame, body, config):
        for label, keypoint in body["pose"].keypoints.items():
            if keypoint.score < config.pose_landmark_dot_confidence_threshold: continue
            cv2.circle(frame, (int(keypoint.point[0]), int(keypoint.point[1])), config.pose_landmark_dot_size, self.__parse_rgb_color(config.pose_landmark_dot_color), config.pose_landmark_dot_size, lineType=cv2.LINE_AA)

        return frame

    def __find_face_rectangle(self, body, config):
        faceRectangle = ((0,0),(0,0))

        if not body["has_face"]:
            return faceRectangle

        #We have a high enough confidence that the face points are real so let's use them to make a rectangle
        #Find the lowest and highest X and then add a few pixels of padding
        lowestY = self.__frame_height
        lowestX = self.__frame_width
        highestY = 0
        highestX = 0

        iter = -1
        for label, keypoint in body["pose"].keypoints.items():
            #faceLabels = {'nose', 'left eye', 'right eye', 'left ear', 'right ear'}
            iter += 1
            if iter < 5:
                if int(keypoint.point[0]) < lowestX: lowestX = int(keypoint.point[0])
                if int(keypoint.point[1]) < lowestY: lowestY = int(keypoint.point[1])
                if int(keypoint.point[0]) > highestX: highestX = int(keypoint.point[0])
                if int(keypoint.point[1]) > highestY: highestY = int(keypoint.point[1])
            else:
                continue

        #Use face position information to determine how to adjust the X coordinates
        xSpread = highestX - lowestX
        ySpread = highestY - lowestY
        if ySpread == 0:
            ySpread = 1
        xFactor = 0

        if body["face_position"] == "Straight":
            lowestX -= 8
            highestX += 8
            xFactor = xSpread / ySpread * 0.8
        elif body["face_position"] == "Right":
            lowestX -= 8
            highestX += (xSpread * 0.75)
            xFactor = xSpread / ySpread * 1.1
        elif body["face_position"] == "Left":
            highestX += 8
            lowestX -= (xSpread * 0.75)
            xFactor = xSpread / ySpread * 1.1
        else:
            lowestX -= 0
            highestX += 0
            xFactor = xSpread / ySpread * 1.0

        yExpand = ySpread * xFactor * config.face_rectangle_y_factor
        lowestY -= yExpand
        highestY += yExpand

        faceRectangle = ((int(lowestX), int(lowestY)), (int(highestX), int(highestY)))

        return faceRectangle

    def __draw_centroid_circles_on_frame(self, frame, body, config):
        centroid = body["tracking_info"]["centroid"]
        text = "OBJECT {}".format(body["body_id"])
        cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.__parse_rgb_color(config.centroid_dots_color), 2, cv2.LINE_AA)
        cv2.circle(frame, (centroid[0], centroid[1]), config.centroid_dots_size, self.__parse_rgb_color(config.centroid_dots_color), config.centroid_dots_size, lineType=cv2.LINE_AA)
        return frame

    def __draw_face_rectangle_on_frame(self, frame, body, config):
        if body["has_face"] and body["face_rectangle"] != ((0,0),(0,0)):
            upperLeft = body["face_rectangle"][0]
            lowerRight = body["face_rectangle"][1]
            cv2.rectangle(frame, upperLeft, lowerRight, self.__parse_rgb_color(config.face_rectangle_color), config.face_rectangle_thickness, lineType=cv2.LINE_AA)
        return frame

    def __parse_rgb_color(self, color_rgb):
        return (color_rgb.blue(), color_rgb.green(), color_rgb.red())

    def __find_body_rectangle(self, body, config):
        bodyRectangle = ((0,0),(0,0))
        
        if body["has_body"]:
            #We have a high enough confidence that the body points are real so let's use them to make a rectangle
            # #Find the lowest and highest X and Y and then add a few pixels of padding
            lowestY = self.__frame_height
            lowestX = self.__frame_width
            highestY = 0
            highestX = 0
            
            iter = -1
            for label, keypoint in body["pose"].keypoints.items():
                iter += 1
                if iter < 5:
                    continue
                else:
                    if int(keypoint.point[0]) < lowestX: lowestX = int(keypoint.point[0])
                    if int(keypoint.point[1]) < lowestY: lowestY = int(keypoint.point[1])
                    if int(keypoint.point[0]) > highestX: highestX = int(keypoint.point[0])
                    if int(keypoint.point[1]) > highestY: highestY = int(keypoint.point[1])

            bodyRectangle = ((int(lowestX - 2), int(lowestY - 2)),(int(highestX + 2), int(highestY + 2)))
            
        return bodyRectangle

    def __determine_if_forehead_visible(self, body, config):
        hasForehead = False
        
        if body["has_face"] and body["face_position"] != "Away":
            hasForehead = True
            
        return hasForehead

    def __determine_face_position(self, body, config):
        #Calculate combo scores of different sets
        pose = body["pose"]
        leftEyeLeftEarScore = (pose.keypoints[1].score + pose.keypoints[3].score) / 2
        rightEyeRightEarScore = (pose.keypoints[2].score + pose.keypoints[4].score) / 2
        eyeAndNoseScore = (pose.keypoints[0].score + pose.keypoints[2].score + pose.keypoints[1].score) / 3
        rightness = leftEyeLeftEarScore - rightEyeRightEarScore
        leftness = rightEyeRightEarScore - leftEyeLeftEarScore
        
        facePosition = 'Unknown'
        
        if body["has_face"]:
            if rightness > (-1 * config.face_position_left_right_threshold) and rightness < config.face_position_left_right_threshold and leftness > (-1 * config.face_position_left_right_threshold) and leftness < config.face_position_left_right_threshold and eyeAndNoseScore >= config.face_position_straight_threshold:
                facePosition = "Straight"
            elif rightness >= config.face_position_left_right_threshold and leftness <= (-1 * config.face_position_left_right_threshold):
                facePosition = "Right"
            elif leftness >= config.face_position_left_right_threshold and rightness <= (-1 * config.face_position_left_right_threshold):
                facePosition = "Left"
            else:
                facePosition = "Away"
        else:
            facePosition = "Away"
            
        return facePosition

    def __determine_forehead_center(self, body, config):
        foreheadCenter = (0,0)
        
        if body["has_forehead"]:
            #Get eye locations
            leftEyeX = int(body["pose"].keypoints[1].point[0])
            leftEyeY = int(body["pose"].keypoints[1].point[1])
            rightEyeX = int(body["pose"].keypoints[2].point[0])
            rightEyeY = int(body["pose"].keypoints[2].point[1])
            
            #Adjust the eye vertical position by 1 pixel if they are exactly equal so we don't have 0 slope
            dY = rightEyeY - leftEyeY
            if dY == 0:
                dY = 1
                
            dX = rightEyeX - leftEyeX
            if dX == 0:
                dX = 1
                
            #Calculate distance between eyes and set distance to forehead
            eyeSlope = dY / dX
            eyeDistance = math.sqrt((dX * dX) + (dY * dY))
            distanceToForehead = eyeDistance * 0.5
            inverseEyeSlope = -1 / eyeSlope
            midX = (leftEyeX + rightEyeX) / 2
            midY = (leftEyeY + rightEyeY) / 2
            endConstant = distanceToForehead / math.sqrt(1 + (inverseEyeSlope * inverseEyeSlope))
            foreheadX = 0
            foreheadY = 0
            
            if eyeSlope < 0:
                foreheadX = int(midX - endConstant)
                foreheadY = int(midY - (endConstant * inverseEyeSlope))
            else:
                foreheadX = int(midX + endConstant)
                foreheadY = int(midY + (endConstant * inverseEyeSlope))
            
            foreheadCenter = (foreheadX, foreheadY)
        
        return foreheadCenter

    def __get_euclidean_distance_between_two_points(self, point1, point2, coordinateCount):
        tmpSum = 0
        
        for i in range(coordinateCount):
            tmpSum += (point1[i] - point2[i]) ** 2
            
        distance = tmpSum ** 0.5
        return distance

    def __add_new_body_to_tracker(self):
        self.__body_number += 1
        self.__body_missing[self.__body_number] = 0
        self.__body_history[self.__body_number] = OrderedDict()
        self.__body_seen[self.__body_number] = OrderedDict()
        
        return self.__body_number

    def __record_body_seen_value_for_current_frame(self, frameNumber, bodyID, seen, config):
        self.__body_seen[bodyID][frameNumber] = seen
        
        if len(self.__body_seen[bodyID]) > config.person_tracking_creation_m:
            self.__body_seen[bodyID].popitem(last=False)

    def __determine_if_body_seen_enough_to_create_person(self, frameNumber, bodyID, config):
        readyForCreation = False
        #We need to see if the key is present for safety otherwise we could throw a "key error"
        if bodyID in self.__body_seen:
            #Shortcut processing by looking if we can possibly have enough "seen" occurrences yet
            if len(self.__body_seen[bodyID]) >= config.person_tracking_creation_n:
                yesCount = 0
                
                for frameNumber, wasSeen in self.__body_seen[bodyID].items():
                    if wasSeen:
                        yesCount += 1
                        
                if yesCount >= config.person_tracking_creation_n:
                    readyForCreation = True
                    
        return readyForCreation

    def __record_body_info_in_tracker_for_id(self, frameNumber, bodyID, bodyInfo, config):
        self.__body_missing[bodyID] = 0
        self.__body_history[bodyID][frameNumber] = bodyInfo
        self.__record_body_seen_value_for_current_frame(frameNumber, bodyID, True, config)
        
        if len(self.__body_history[bodyID]) > config.object_tracking_info_history_count:
            self.__body_history[bodyID].popitem(last=False)

    def __process_cleanup_of_missing_bodies(self, curFrame, config):
        #Loop through the entries for missing bodies and find any that have been missing too long
        for bodyID in list(self.__body_missing.keys()):
            if self.__body_missing[bodyID] > config.object_tracking_removal_count and bodyID in self.__person_data:
                personData = self.__person_data[bodyID]
                person_id = personData["uuid"] 

                #EMIT PERSON GONE EVENT
                self.emit("person_left_scene", person_id)
                
                del self.__body_missing[bodyID]
                del self.__body_history[bodyID]
                del self.__body_seen[bodyID]
                del self.__person_data[bodyID]

    def __mark_unmatched_body_ids_as_missing(self, currentFrameNumber, config):
        #Loop through the body history and see if any do not have matches for the current frame
        for bodyID in list(self.__body_history.keys()):
            if currentFrameNumber in self.__body_history[bodyID]:
                continue
            else:
                self.__body_missing[bodyID] += 1
                self.__record_body_seen_value_for_current_frame(currentFrameNumber, bodyID, False, config)

    def __check_if_person_data_record_exists_for_body_id(self, bodyID):
        if bodyID in self.__person_data:
            return True
        else:
            return False

    def __create_new_person_data_record_with_body_id(self, bodyID, config):
        #Use UUID version 4 (full random) and just take the first 8 characters
        personUUID = str(uuid.uuid4())[0:8]
        
        #Create standard dictionary for storing person data with default values
        #The detection history fields are ordered dictionary objects because we will need to pop old readings off the list
        data = {}
        data["uuid"] = personUUID
        data["is_poi"] = False
        
        self.__person_data[bodyID] = data

        #EMIT NEW PERSON EVENT
        self.emit("new_person_entered_scene", personUUID)

    def __generate_tracking_info_for_body(self, frame, body, config):
        trackingInfo = {}
        centroid = (0,0)
        size = (0,0)
        averageColor = (0,0,0)
        
        startX = 0
        startY = 0
        endX = 0
        endY = 0
        
        if body["has_face"]:
            startX = body["face_rectangle"][0][0]
            startY = body["face_rectangle"][0][1]
            endX = body["face_rectangle"][1][0]
            endY = body["face_rectangle"][1][1]
        else:
            startX = body["body_rectangle"][0][0]
            startY = body["body_rectangle"][0][1]
            endX = body["body_rectangle"][1][0]
            endY = body["body_rectangle"][1][1]
            
        sizeW = int(endX - startX)
        sizeH = int(endY - startY)
        centroidX = int((startX + endX) / 2)
        centroidY = int((startY + endY) / 2)
        
        size = (sizeW, sizeH)
        centroid = (centroidX, centroidY)
        
        centroidColorSampleStartX = max(centroidX - int(config.object_tracking_color_sample_pixels / 2), 0)
        centroidColorSampleEndX = min(centroidX + int(config.object_tracking_color_sample_pixels / 2), self.__frame_width)
        centroidColorSampleStartY = max(centroidY - int(config.object_tracking_color_sample_pixels / 2), 0)
        centroidColorSampleEndY = min(centroidY + int(config.object_tracking_color_sample_pixels / 2), self.__frame_height)
        
        centroidColorSampleStartX = min(centroidColorSampleStartX, (self.__frame_width - 1))
        centroidColorSampleEndX = max(centroidColorSampleEndX, 1)
        centroidColorSampleStartY = min(centroidColorSampleStartY, (self.__frame_height - 1))
        centroidColorSampleEndY = max(centroidColorSampleEndY, 1)

        colorSampleChunk = frame[centroidColorSampleStartY : centroidColorSampleEndY, centroidColorSampleStartX : centroidColorSampleEndX]
        
        #Find the average pixel color values for BGR
        avgBlue = 0
        avgGreen = 0
        avgRed = 0
        
        avg_color_per_row = np.average(colorSampleChunk, axis=0)
        avg_color = np.average(avg_color_per_row, axis=0)
        avgBlue = int(avg_color[0])
        avgGreen = int(avg_color[1])
        avgRed = int(avg_color[2])
        
        averageColor = (avgBlue, avgGreen, avgRed)
        
        trackingInfo["size"] = size
        trackingInfo["centroid"] = centroid
        trackingInfo["color"] = averageColor
        
        return trackingInfo

    def __apply_best_object_matches_to_body_tracking_info(self, currentFrameNumber, bodies, config):
        for body in bodies:
            trackingInfo = body["tracking_info"]
            scoreList = OrderedDict()
            lowestScore = 1000
            
            #Loop through existing body ID histories and compute matching
            for existingBodyID in list(self.__body_history.keys()):
                #Loop through the history - keys will be frame numbers - and throw out history entries that are too old
                #List will be oldest entries first
                historyNum = 0
                vectorX = 0
                vectorY = 0
                priorX = 0
                priorY = 0
                cumCentroidDistance = 0
                cumColorDistance = 0
                cumSizeDistance = 0
                cumCentroidWithVectorDistance = 0
                
                for historyFrameNumber in list(self.__body_history[existingBodyID].keys()):
                    #This history entry is valid - proceed
                    historyNum += 1
                    
                    #First add to the vector if we are not on the first history frame
                    if historyNum > 1:
                        vectorX += (self.__body_history[existingBodyID][historyFrameNumber]["centroid"][0] - priorX)
                        vectorY += (self.__body_history[existingBodyID][historyFrameNumber]["centroid"][1] - priorY)
                        
                    priorX = self.__body_history[existingBodyID][historyFrameNumber]["centroid"][0]
                    priorY = self.__body_history[existingBodyID][historyFrameNumber]["centroid"][1]
                    
                    cumCentroidDistance += self.__get_euclidean_distance_between_two_points(self.__body_history[existingBodyID][historyFrameNumber]["centroid"], trackingInfo["centroid"], 2)
                    cumColorDistance += self.__get_euclidean_distance_between_two_points(self.__body_history[existingBodyID][historyFrameNumber]["color"], trackingInfo["color"], 3)
                    cumSizeDistance += self.__get_euclidean_distance_between_two_points(self.__body_history[existingBodyID][historyFrameNumber]["size"], trackingInfo["size"], 2)
                    
                if historyNum > 1:
                    vectorX = vectorX / (historyNum - 1)
                    vectorY = vectorY / (historyNum - 1)
                    
                projectedX = priorX + vectorX
                projectedY = priorY + vectorY
                
                cumCentroidWithVectorDistance = self.__get_euclidean_distance_between_two_points((projectedX, projectedY), trackingInfo["centroid"], 2)
                
                cumCentroidDistance = cumCentroidDistance / historyNum
                cumColorDistance = cumColorDistance / historyNum
                cumSizeDistance = cumSizeDistance / historyNum
                
                totalCurrentScore = (config.object_tracking_centroid_weight * cumCentroidDistance) + (config.object_tracking_color_weight * cumColorDistance) + (config.object_tracking_vector_weight * cumCentroidWithVectorDistance) + (config.object_tracking_size_weight * cumSizeDistance)
                scoreList[existingBodyID] = totalCurrentScore
                if totalCurrentScore < lowestScore:
                    lowestScore = totalCurrentScore
                    
            body["score_list"] = scoreList
            body["lowest_score"] = lowestScore
            
        #Loop through the objects and find the lowest score that is also the lowest score for that body
        for existingBodyID in list(self.__body_history.keys()):
            objLowestScore = 1000
            objBestBodyIterator = -1
            bodyIter = -1
            
            for body in bodies:
                bodyIter += 1
                thisObjScore = body["score_list"][existingBodyID]
                
                if thisObjScore < objLowestScore and body["lowest_score"] == thisObjScore:
                    objLowestScore = thisObjScore
                    objBestBodyIterator = bodyIter
                    
            if objBestBodyIterator > -1:
                self.__record_body_info_in_tracker_for_id(currentFrameNumber, existingBodyID, bodies[objBestBodyIterator]["tracking_info"], config)
                bodies[objBestBodyIterator]["body_id"] = existingBodyID
                
                #Check if we have a person data record yet
                hasPerson = self.__check_if_person_data_record_exists_for_body_id(existingBodyID)
                
                if hasPerson:
                    #Add the person ID to the body
                    bodies[objBestBodyIterator]["person_id"] = existingBodyID
                else:
                    #See if we can create one based on our appearance history
                    personReady = self.__determine_if_body_seen_enough_to_create_person(currentFrameNumber, existingBodyID, config)
                    self.__create_new_person_data_record_with_body_id(existingBodyID, config)
                    bodies[objBestBodyIterator]["person_id"] = existingBodyID
                    
        #Loop through bodies one last time to see if any do not have an object ID yet
        for body in bodies:
            if body["body_id"] == 0:
                newObjectID = self.__add_new_body_to_tracker()
                body["body_id"] = newObjectID
                self.__body_history[newObjectID][currentFrameNumber] = body["tracking_info"]
                self.__body_missing[newObjectID] = 0

    def __set_person_as_poi(self, personID, frameNumber, body, config):
        self.__prior_poi_id = personID
        
        for curPersonID in self.__person_data:
            if curPersonID == personID:
                self.__person_data[personID]['is_poi'] = True
            else:
                self.__person_data[personID]['is_poi'] = False
                
        #EMIT NEW POI EVENT
        person_uuid = self.__person_data[personID]["uuid"]
        self.emit("new_person_in_front", person_uuid)

    def __draw_person_data_on_frame(self, frame, body, config):
        if not body["person_id"] in self.__person_data:
            return frame
            
        #Get data to display
        personIdValue = self.__person_data[body["person_id"]]["uuid"]
        
        #Assemble output text strings
        identityText = "{}{}".format(config.identity_text_prefix, personIdValue)
        
        #Calculate total height from which lines of text are being shown
        idWidth = 0
        idHeight = 0
        idBaseLine = 0
        
        if config.show_person_id:
            (idWidth, idHeight), idBaseLine = cv2.getTextSize(identityText, cv2.FONT_HERSHEY_SIMPLEX, config.person_data_identity_text_font_size, config.person_data_identity_text_stroke)
            
        #Add line and baseline heights together to find the total height
        totalTextHeightWithBaselines = int(idHeight + idBaseLine)
        halfHeight = int(totalTextHeightWithBaselines / 2)
        
        #Get forehead X,Y position for this body
        foreheadCenter = body["forehead_center"]
        
        #Determine end coordinates for data line
        lineEndX = foreheadCenter[0] + config.person_data_text_offset_x
        lineEndY = 0
        textStartY = 0
        
        if config.person_data_text_offset_y <= 0:
            lineEndY = foreheadCenter[1] + config.person_data_text_offset_y - halfHeight
            textStartY = foreheadCenter[1] + config.person_data_text_offset_y - totalTextHeightWithBaselines
        else:
            lineEndY = foreheadCenter[1] + config.person_data_text_offset_y + halfHeight
            textStartY = foreheadCenter[1] + config.person_data_text_offset_y
            
        #Draw line from forehead center to person data text box
        cv2.line(frame, foreheadCenter, (lineEndX, lineEndY), self.__parse_rgb_color(config.person_data_line_color), config.person_data_line_thickness, lineType=cv2.LINE_AA)
        
        if config.show_person_id:
            idWriteY = textStartY + idHeight + idBaseLine
            cv2.putText(frame, identityText, (lineEndX, idWriteY), cv2.FONT_HERSHEY_SIMPLEX, config.person_data_identity_text_font_size, self.__parse_rgb_color(config.person_data_identity_text_color), config.person_data_identity_text_stroke, cv2.LINE_AA)
        
        return frame
