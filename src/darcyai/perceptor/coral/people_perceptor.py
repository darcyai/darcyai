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
import os
import pathlib

from darcyai.utils import validate_type, validate

from darcyai.perceptor.coral.coral_perceptor_base import CoralPerceptorBase
from darcyai.perceptor.people_perceptor_base import PeoplePerceptorBase, PoseEngine

class PeoplePerceptor(CoralPerceptorBase, PeoplePerceptorBase):
    """
    Perceptor for detecting people in an image.

    # Perceptor Config:
        minimum_face_threshold (float):
            Confidence threshold for detecting the face as a percent certainty
            Default value: 0.4

        minimum_body_threshold (float):
            Confidence threshold for detecting the body as a percent certainty
            Default value: 0.2

        minimum_face_height (int):
            The minimum height of the persons face in pixels that we want to work with
            Default value: 20

        minimum_body_height (int):
            The minimum height of the persons body in pixels that we want to work with
            Default value: 120

        show_pose_landmark_dots (bool):
            Show pose landmark dots (nose, ears, elbows, etc.)
            Default value: False

        show_body_rectangle (bool):
            Draw a rectangle around the persons body
            Default value: False

        show_face_rectangle (bool):
            Draw a rectangle around the persons face
            Default value: False

        face_rectangle_color (rgb):
            Color of the face rectangle
            Default value: RGB(255, 0, 0)

        face_rectangle_thickness (int):
            Thickness of the face rectangle
            Default value: 1

        body_rectangle_color (rgb):
            Color of the body rectangle
            Default value: RGB(0, 255, 0)

        body_rectangle_thickness (int):
            Thickness of the body rectangle
            Default value: 1

        pose_landmark_dot_confidence_threshold (float):
            Confidence threshold for identifying pose landmarks as a percent certainty
            Default value: 0.5

        pose_landmark_dot_size (int):
            Size of the pose landmark dots
            Default value: 1

        pose_landmark_dot_color (rgb):
            Color of the pose landmark dots
            Default value: RGB(255, 255, 255)

        show_face_position_arrow (bool):
            Show the arrow that indicates which direction the person is looking
            Default value: False

        face_position_arrow_color (rgb):
            Color of the face position arrow
            Default value: RGB(255, 255, 255)

        face_position_arrow_stroke (int):
            Thickness of the face position arrow
            Default value: 1

        face_position_arrow_offset_x (int):
            X offset for the face position arrow
            Default value: 0

        face_position_arrow_offset_y (int):
            Y offset for the face position arrow
            Default value: -30

        face_position_arrow_length (int):
            Length of the face position arrow
            Default value: 20

        face_position_left_right_threshold (float):
            Threshold for detecting if the person is looking left or right
            Default value: 0.3

        face_position_straight_threshold (float):
            Threshold for detecting if the person is looking straight
            Default value: 0.7

        show_forehead_center_dot (bool):
            Show a dot in the center of the persons forehead
            Default value: False

        forehead_center_dot_color (rgb):
            Color of the forehead center dot
            Default value: RGB(255, 255, 255)

        forehead_center_dot_size (int):
            Size of the forehead center dot
            Default value: 1

        face_rectangle_y_factor (float):
            Size adjustment factor for the height of the persons face, which can be used to make sure objects like hair and hats are captured
            Default value: 1.0

        show_centroid_dots (bool):
            Show centroid information (center of the face or body)
            Default value: False

        centroid_dots_color (rgb):
            Color of the centroid information
            Default value: RGB(255, 255, 255)

        centroid_dots_size (int):
            Size of the centroid information
            Default value: 1

        object_tracking_allowed_missed_frames (int):
            Object tracking allowed missed frames
            Default value: 50

        object_tracking_color_sample_pixels (int):
            Number of pixels to use for color sampling when tracking objects
            Default value: 4

        object_tracking_info_history_count (int):
            Number of video frames used to track an object in the field of view
            Default value: 3

        object_tracking_removal_count (int):
            Number of frames to wait before removing an object from tracking
            Default value: 50

        object_tracking_centroid_weight (float):
            Level of importance that centroid data has when tracking objects
            Default value: 0.25

        object_tracking_color_weight (float):
            Level of importance that color data has when tracking objects
            Default value: 0.25

        object_tracking_vector_weight (float):
            Level of importance that vector data has when tracking objects
            Default value: 0.25

        object_tracking_size_weight (float):
            Level of importance that size data has when tracking objects
            Default value: 0.25

        object_tracking_creation_m (int):
            Minimum number of frames out of N frames that an object must be present in the field of view before it is tracked
            Default value: 10

        object_tracking_creation_n (int):
            Total number of frames used to evaluate an object before it is tracked
            Default value: 7

        person_tracking_creation_m (int):
            Minimum number of frames out of N frames needed to promote a tracked object to a person
            Default value: 20

        person_tracking_creation_m (int):
            Total number of frames used to evaluate a tracked object before it is promoted to a person
            Default value: 16

        show_person_id (bool):
            Show anonymous unique identifier for the person
            Default value: False

        person_data_line_color (rgb):
            Color of the person data line
            Default value: RGB(255, 255, 255)

        person_data_line_thickness (int):
            Thickness of the person data line
            Default value: 1

        person_data_identity_text_color (rgb):
            Color of the person data identity text
            Default value: RGB(255, 255, 255)

        person_data_identity_text_stroke (int):
            Thickness of the person data identity text
            Default value: 1

        person_data_identity_text_font_size (float):
            Font size of the person data identity text
            Default value: 1.0

        person_data_text_offset_x (int):
            X offset of the person data text
            Default value: 30

        person_data_text_offset_y (int):
            Y offset of the person data text
            Default value: -40

        identity_text_prefix (str):
            Text information that you want to display at the beginning of the person ID
            Default value: Person ID:

        rolling_video_storage_frame_count (int):
            Number of the video frames to store while processing
            Default value: 100

    # Events:
        new_person_entered_scene
        person_facing_new_direction
        new_person_in_front
        person_left_scene
        identity_determined_for_person
        person_got_too_close
        person_went_too_far_away
        max_person_count_reached
        person_count_fell_below_maximum
        person_occluded
    """
    def __init__(self, **kwargs):
        CoralPerceptorBase.__init__(self, **kwargs)

        self.__primary_pose_engine = None

    def run(self, input_data, config):
        return PeoplePerceptorBase.run(self, input_data, config, self.__primary_pose_engine)
    
    def load(self, accelerator_idx:[int, None]) -> None:
        script_dir = pathlib.Path(__file__).parent.absolute()
        model_file = os.path.join(script_dir, "models/posenet.tflite")

        minimum_body_threshold = self.get_config_value("minimum_body_threshold")
        
        if accelerator_idx is None:
            self.__primary_pose_engine = PoseEngine(model_file,
                                                    minimum_pose_threshold=minimum_body_threshold)
        else:
            validate_type(accelerator_idx, int, "accelerator_idx must be an integer")
            validate(accelerator_idx >= 0, "accelerator_idx must be greater than or equal to 0")

            #TODO: implement accelerator index pass-through to PoseEngine class above
            self.__primary_pose_engine = PoseEngine(model_file,
                                                    tpu=True,
                                                    minimum_pose_threshold=minimum_body_threshold)
        
        super().set_loaded(True)        
