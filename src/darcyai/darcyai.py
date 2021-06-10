import cv2
import math
import numpy as np
import os
import threading
import time
import traceback
import uuid
import pathlib
from collections import OrderedDict
from edgetpu.basic import edgetpu_utils
from edgetpu.basic.basic_engine import BasicEngine
from flask import Flask, request, Response
from imutils.video import VideoStream
from darcyai.pose_engine import PoseEngine
from darcyai.config import DarcyAIConfig
from darcyai.object import DetectedObject


class DarcyAI:
    def __init__(
                 self,
                 data_processor=None,
                 frame_processor=None,
                 do_perception=True,
                 custom_perception_model=None,
                 config=DarcyAIConfig()):
        """
        Initializes DarcyAI Module

        :param data_processor: Callback method to call with detected bodies and PoseNet raw data 
        :param custom_perception_model: User's model to deploy on EdgeTPU
        :param config: Instance of DarcyAIConfig
        """

        if do_perception and data_processor is None:
            raise Exception("data_processor callback is required")

        self.__data_processor = data_processor
        self.__frame_processor = frame_processor
        self.__custom_perception_model = custom_perception_model
        self.__config = config
        self.__do_perception = do_perception

        if not custom_perception_model is None:
            self.__custom_perception_engine = BasicEngine(custom_perception_model)
            input_shape = self.__custom_perception_engine.get_input_tensor_shape()
            self.__custom_model_inference_shape = (input_shape[2], input_shape[1])

        self.__custom_engine = None
        self.__custom_engine_inference_size = None

        self.__persons_history = OrderedDict()

        # initialize video camera
        self.__frame_width = 640
        self.__frame_height = 480
        self.__vs = self.__initialize_video_stream()

        self.__frame_history = OrderedDict()
        self.__frame_number = 0
        self.__latest_frame = None

        self.__object_number = 0
        self.__object_history = OrderedDict()
        self.__object_missing = OrderedDict()
        self.__object_count = OrderedDict()
        self.__object_seen = OrderedDict()
        self.__object_data = OrderedDict()

        self.__api = Flask(__name__)

        script_dir = pathlib.Path(__file__).parent.absolute()
        model_path = os.path.join(script_dir, 'models', 'posenet.tflite')
        (self.__pose_engine, self.__object_detection_inference_size) = self.__get_engine(model_path)


    def __get_engine(self, path):
        """Initializes object detection engine.

        path: Path to TFLite model
        """

        engine = PoseEngine(model_path=path)
        input_shape = engine.get_input_tensor_shape()
        inference_size = (input_shape[2], input_shape[1])

        return (engine, inference_size)


    def __initialize_video_stream(self):
        """Initialize and return VideoStream
        """

        vs = VideoStream(usePiCamera=True, resolution=(self.__frame_width, self.__frame_height), framerate=20).start()
        test_frame = vs.read()
        counter = 0
        while test_frame is None:
            if counter == 10:
                os._exit(1)

            #Give the camera unit a couple of seconds to start
            print("Waiting for camera unit to start...")
            counter += 1
            time.sleep(1)
            test_frame = vs.read()

        return vs


    def __add_current_frame_to_rolling_history(self, frame):
        """Adds current frame to frame histort.

        frame: Current frame
        """
        milltime = int(round(time.time() * 1000))
        current_frame = {"timestamp" : milltime, "frame" : frame.copy()}
        self.__frame_history[self.__frame_number] = current_frame

        # TODO: make max frames buffer size configurable
        if len(self.__frame_history) > 100:
            self.__frame_history.popitem(last=False)


    def __add_new_object_to_tracker(self):
        """Adds an object to tracker.
        """
        self.__object_number += 1

        self.__object_missing[self.__object_number] = 0
        self.__object_history[self.__object_number] = OrderedDict()
        self.__object_seen[self.__object_number] = OrderedDict()

        return self.__object_number


    def __record_object_seen_value_for_current_frame(self, frame_number, object_id, seen):
        """Sets the object seen/unseen in current frame.

        frame_number: Current frame number  
        object_id: Id of the object to set the flag for  
        seen: True/False
        """
        self.__object_seen[object_id][frame_number] = seen

        if len(self.__object_seen[object_id]) > self.__config.GetPersonTrackingCreationM():
            self.__object_seen[object_id].popitem(last=False)


    def __determine_if_object_seen_enough_to_create_person(self, frame_number, object_id):
        """Sets object as seen when it exists in the frame for a while.

        frame_number: current frame number  
        object_id: id of the object
        """
        ready_for_creation = False

        # We need to see if the key is present for safety otherwise we could throw a "key error"
        if object_id in self.__object_seen:
            # Shortcut processing by looking if we can possibly have enough "seen" occurrences yet
            if len(self.__object_seen[object_id]) >= self.__config.GetPersonTrackingCreationN():
                yes_count = 0

                for frame_number, was_seen in self.__object_seen[object_id].items():
                    if was_seen:
                       yes_count += 1

                if yes_count >= self.__config.GetPersonTrackingCreationN():
                    ready_for_creation = True

        return ready_for_creation


    def __record_object_info_in_tracker_for_id(self, frame_number, object_id, object_info):
        self.__object_missing[object_id] = 0
        self.__object_history[object_id][frame_number] = object_info
        self.__record_object_seen_value_for_current_frame(frame_number, object_id, True)

        if len(self.__object_history[object_id]) > self.__config.GetObjectTrackingInfoHistoryCount():
            self.__object_history[object_id].popitem(last=False)


    def __process_cleanup_of_missing_objects(self):
        for object_id in list(self.__object_missing.keys()):
            if self.__object_missing[object_id] > self.__config.GetObjectTrackingRemovalCount() and object_id in self.__object_data:
                object_data = self.__object_data[object_id]

                del self.__object_missing[object_id]
                del self.__object_history[object_id]
                del self.__object_seen[object_id]
                del self.__object_data[object_id]


    def __mark_unmatched_object_ids_as_missing(self, current_frame_number):
        # Loop through the object history and see if any do not have matches for the current frame
        for object_id in list(self.__object_history.keys()):
            if current_frame_number in self.__object_history[object_id]:
                continue
            else:
                self.__object_missing[object_id] += 1
                self.__record_object_seen_value_for_current_frame(current_frame_number, object_id, False)


    def __check_if_object_data_record_exists_for_object_id(self, object_id):
        if object_id in self.__object_data:
            return True
        else:
            return False


    def __create_new_object_data_record_with_object_id(self, object_id, object_uuid):
        # Create standard dictionary for storing person data with default values
        # The detection history fields are ordered dictionary objects because we will need to pop old readings off the list
        data = {}
        data["uuid"] = object_uuid

        self.__object_data[object_id] = data


    def __apply_best_object_matches_to_object_tracking_info(self, current_frame_number, objects):
        for object in objects:
            tracking_info = object.tracking_info
            score_list = OrderedDict()
            lowest_score = 1000

            # Loop through existing object ID histories and compute matching
            for existing_object_id in list(self.__object_history.keys()):
                #Loop through the history - keys will be frame numbers - and throw out history entries that are too old
                #List will be oldest entries first
                history_num = 0
                vector_x = 0
                vector_y = 0
                prior_x = 0
                prior_y = 0
                cum_centroid_distance = 0
                cum_color_distance = 0
                cum_size_distance = 0
                cum_centroid_with_vector_distance = 0

                for history_frame_number in list(self.__object_history[existing_object_id].keys()):
                    # This history entry is valid - proceed
                    history_num += 1

                    # First add to the vector if we are not on the first history frame
                    if history_num > 1:
                        vector_x += (self.__object_history[existing_object_id][history_frame_number]["centroid"][0] - prior_x)
                        vector_y += (self.__object_history[existing_object_id][history_frame_number]["centroid"][1] - prior_y)

                    prior_x = self.__object_history[existing_object_id][history_frame_number]["centroid"][0]
                    prior_y = self.__object_history[existing_object_id][history_frame_number]["centroid"][1]

                    cum_centroid_distance += self.__get_euclidean_distance_between_two_points(self.__object_history[existing_object_id][history_frame_number]["centroid"], tracking_info["centroid"], 2)
                    cum_color_distance += self.__get_euclidean_distance_between_two_points(self.__object_history[existing_object_id][history_frame_number]["color"], tracking_info["color"], 3)
                    cum_size_distance += self.__get_euclidean_distance_between_two_points(self.__object_history[existing_object_id][history_frame_number]["size"], tracking_info["size"], 2)

                if history_num > 1:
                    vector_x = vector_x / (history_num - 1)
                    vector_y = vector_y / (history_num - 1)

                projected_x = prior_x + vector_x
                projected_y = prior_y + vector_y

                cum_centroid_with_vector_distance = self.__get_euclidean_distance_between_two_points((projected_x, projected_y), tracking_info["centroid"], 2)

                cum_centroid_distance = cum_centroid_distance / history_num
                cum_color_distance = cum_color_distance / history_num
                cum_size_distance = cum_size_distance / history_num

                total_current_score = (self.__config.GetObjectTrackingCentroidWeight() * cum_centroid_distance) + (self.__config.GetObjectTrackingColorWeight() * cum_color_distance) + (self.__config.GetObjectTrackingVectorWeight() * cum_centroid_with_vector_distance) + (self.__config.GetObjectTrackingSizeWeight() * cum_size_distance)
                score_list[existing_object_id] = total_current_score
                if total_current_score < lowest_score:
                    lowest_score = total_current_score

            object.score_list = score_list
            object.lowest_score = lowest_score

        # Loop through the objects and find the lowest score that is also the lowest score for that object
        for existing_object_id in list(self.__object_history.keys()):
            obj_lowest_score = 1000
            obj_best_object_iterator = -1
            object_iter = -1

            for object in objects:
                object_iter += 1
                this_obj_score = object.score_list[existing_object_id]

                if this_obj_score < obj_lowest_score and object.lowest_score == this_obj_score:
                    obj_lowest_score = this_obj_score
                    obj_best_object_iterator = object_iter

            if obj_best_object_iterator > -1:
                self.__record_object_info_in_tracker_for_id(current_frame_number, existing_object_id, objects[obj_best_object_iterator].tracking_info)
                objects[obj_best_object_iterator].object_id = existing_object_id
                #Check if we have a person data record yet
                has_object = self.__check_if_object_data_record_exists_for_object_id(existing_object_id)
                if has_object:
                    #Add the person ID to the object
                    objects[obj_best_object_iterator].object_id = existing_object_id
                else:
                    #See if we can create one based on our appearance history
                    object_ready = self.__determine_if_object_seen_enough_to_create_person(current_frame_number, existing_object_id)
                    object_uuid = str(uuid.uuid4())[0:8]
                    self.__create_new_object_data_record_with_object_id(existing_object_id, object_uuid)
                    objects[obj_best_object_iterator].object_id = existing_object_id
                    objects[obj_best_object_iterator].uuid = object_uuid


        #Loop through objects one last time to see if any do not have an object ID yet
        for object in objects:
            if object.object_id == 0:
                new_object_id = self.__add_new_object_to_tracker()
                object.object_id = new_object_id
                self.__object_history[new_object_id][current_frame_number] = object.tracking_info
                self.__object_missing[new_object_id] = 0


    def __get_euclidean_distance_between_two_points(self, point1, point2, coordinate_count):
        tmp_sum = 0

        for i in range(coordinate_count):
            tmp_sum += (point1[i] - point2[i]) ** 2
        
        distance = tmp_sum ** 0.5

        return distance


    def __generate_tracking_info_for_object(self, frame, body):
        tracking_info = {}
        centroid = (0,0)
        size = (0,0)
        average_color = (0,0,0)

        (start_x, start_y), (end_x, end_y) = self.__get_object_bounding_box(body)

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

        centroid_color_sample_start_x = max(centroid_x - int(self.__config.GetObjectTrackingColorSamplePixels() / 2), 0)
        centroid_color_sample_end_x = min(centroid_x + int(self.__config.GetObjectTrackingColorSamplePixels() / 2), self.__frame_width)
        centroid_color_sample_start_y = max(centroid_y - int(self.__config.GetObjectTrackingColorSamplePixels() / 2), 0)
        centroid_color_sample_end_y = min(centroid_y + int(self.__config.GetObjectTrackingColorSamplePixels() / 2), self.__frame_height)

        color_sample_chunk = frame[centroid_color_sample_start_y : centroid_color_sample_end_y, centroid_color_sample_start_x : centroid_color_sample_end_x]

        #Find the average pixel color values for BGR
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


    def __encode_jpeg(self, frame):
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 100]
        img_encode = cv2.imencode(".jpg", frame, encode_param)[1]
        data_encode = np.array(img_encode)
        return data_encode.tobytes()


    def __get_object_bounding_box(self, body):
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

        return (start_x, start_y), (end_x, end_y)


    def __generate_stream(self):
        while True:
            try:
                while self.__latest_frame is None:
                    time.sleep(0.10)
                    continue

                time.sleep(1.0 / 10)
                frame = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + self.__encode_jpeg(self.__latest_frame)
                yield(frame)
            except Exception as e:
                tb = traceback.format_exc()
                print("Error at generating stream {}".format(tb))
                pass


    def __live_feed(self): 
        response = Response(self.__generate_stream(), 
                            mimetype="multipart/x-mixed-replace; boundary=frame") 
        
        return response


    def __start_api_server(self):
        ssl_context = None
        self.__api.add_url_rule("/live-feed", "__live_feed", self.__live_feed)
        self.__api.run(
            host="0.0.0.0",
            port=self.__config.GetLiveStreamPort(),
            ssl_context=ssl_context,
            debug=False)


    def __get_qualified_body_detections(self, poses):
        #Loop through all raw detected poses and return an array of qualified body dictionaries
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
            faceScore = (pose.keypoints['nose'].score + pose.keypoints['left eye'].score + pose.keypoints['right eye'].score + pose.keypoints['left ear'].score + pose.keypoints['right ear'].score) / 5
            bodyScore = (pose.keypoints['left shoulder'].score + pose.keypoints['right shoulder'].score + pose.keypoints['left elbow'].score + pose.keypoints['right elbow'].score + pose.keypoints['left wrist'].score + pose.keypoints['right wrist'].score + pose.keypoints['left hip'].score + pose.keypoints['right hip'].score + pose.keypoints['left knee'].score + pose.keypoints['right knee'].score + pose.keypoints['left ankle'].score + pose.keypoints['right ankle'].score) / 12

            #Evaluate confidence levels first
            if faceScore >= self.__config.GetPoseMinimumFaceThreshold():
                meetsConfidence = True
                curBody["has_face"] = True
                curBody["face_score"] = faceScore
            
            if bodyScore >= self.__config.GetPoseMinimumBodyThreshold():
                meetsConfidence = True
                curBody["has_body"] = True
                curBody["body_score"] = bodyScore

            #Now check for size requirements
            if meetsConfidence:
                #Get face and body sizes from keypoint coordinates in rough estimate style
                faceHeight = ((pose.keypoints['left shoulder'].yx[0] + pose.keypoints['right shoulder'].yx[0]) / 2) - ((pose.keypoints['left eye'].yx[0] + pose.keypoints['right eye'].yx[0]) / 2)
                bodyHeight = ((pose.keypoints['left ankle'].yx[0] + pose.keypoints['right ankle'].yx[0]) / 2) - pose.keypoints['nose'].yx[0]

                if faceHeight >= self.__config.GetPoseMinimumFaceHeight():
                    meetsSize = True
                    curBody["simple_face_height"] = faceHeight

                if bodyHeight >= self.__config.GetPoseMinimumBodyHeight():
                    meetsSize = True
                    curBody["simple_body_height"] = bodyHeight

                #If we meet both size and confidence requirements, put this body in the output set
                if meetsSize:
                    curBody["pose"] = pose
                    bodies.append(curBody)

        return bodies


    def __determine_face_position(self, body):
        #Calculate combo scores of different sets
        pose = body["pose"]
        leftEyeLeftEarScore = (pose.keypoints['left eye'].score + pose.keypoints['left ear'].score) / 2
        rightEyeRightEarScore = (pose.keypoints['right eye'].score + pose.keypoints['right ear'].score) / 2
        eyeAndNoseScore = (pose.keypoints['nose'].score + pose.keypoints['right eye'].score + pose.keypoints['left eye'].score) / 3
        rightness = leftEyeLeftEarScore - rightEyeRightEarScore
        leftness = rightEyeRightEarScore - leftEyeLeftEarScore

        facePosition = 'Unknown'

        if body["has_face"]:
            if rightness > (-1 * self.__config.GetFacePositionLeftRightThreshold()) and rightness < self.__config.GetFacePositionLeftRightThreshold() and leftness > (-1 * self.__config.GetFacePositionLeftRightThreshold()) and leftness < self.__config.GetFacePositionLeftRightThreshold() and eyeAndNoseScore >= self.__config.GetFacePositionStraightThreshold():
                facePosition = "Straight"
            elif rightness >= self.__config.GetFacePositionLeftRightThreshold() and leftness <= (-1 * self.__config.GetFacePositionLeftRightThreshold()):
                facePosition = "Right"
            elif leftness >= self.__config.GetFacePositionLeftRightThreshold() and rightness <= (-1 * self.__config.GetFacePositionLeftRightThreshold()):
                facePosition = "Left"
            else:
                facePosition = "Away"
        else:
            facePosition = "Away"

        return facePosition


    def __determine_if_forehead_visible(self, body):
        hasForehead = False

        if body["has_face"] and body["face_position"] != "Away":
            hasForehead = True

        return hasForehead


    def __determine_forehead_center(self, body):
        foreheadCenter = (0,0)

        if body["has_forehead"]:
            #Get eye locations
            leftEyeX = int(body["pose"].keypoints["left eye"].yx[1])
            leftEyeY = int(body["pose"].keypoints["left eye"].yx[0])
            rightEyeX = int(body["pose"].keypoints["right eye"].yx[1])
            rightEyeY = int(body["pose"].keypoints["right eye"].yx[0])
            
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


    def __find_body_rectangle(self, body):
        bodyRectangle = ((0,0),(0,0))

        if body["has_body"]:
            #We have a high enough confidence that the body points are real so let's use them to make a rectangle
            #Find the lowest and highest X and Y and then add a few pixels of padding
            lowestY = self.__frame_height
            lowestX = self.__frame_width
            highestY = 0
            highestX = 0

            for label, keypoint in body["pose"].keypoints.items():
                faceLabels = {'nose', 'left eye', 'right eye', 'left ear', 'right ear'}
                if label in faceLabels:
                    continue
                else:
                    if keypoint.yx[1] < lowestX: lowestX = keypoint.yx[1]
                    if keypoint.yx[0] < lowestY: lowestY = keypoint.yx[0]
                    if keypoint.yx[1] > highestX: highestX = keypoint.yx[1]
                    if keypoint.yx[0] > highestY: highestY = keypoint.yx[0]

            bodyRectangle = ((int(lowestX - 2), int(lowestY - 2)),(int(highestX + 2), int(highestY + 2)))

        return bodyRectangle


    def __find_face_rectangle(self, body):
        faceRectangle = ((0,0),(0,0))

        if not body["has_face"]:
            return faceRectangle

        #We have a high enough confidence that the face points are real so let's use them to make a rectangle
        #Find the lowest and highest X and then add a few pixels of padding
        lowestY = self.__frame_height
        lowestX = self.__frame_width
        highestY = 0
        highestX = 0

        for label, keypoint in body["pose"].keypoints.items():
            faceLabels = {'nose', 'left eye', 'right eye', 'left ear', 'right ear'}
            if label in faceLabels:
                if keypoint.yx[1] < lowestX: lowestX = keypoint.yx[1]
                if keypoint.yx[0] < lowestY: lowestY = keypoint.yx[0]
                if keypoint.yx[1] > highestX: highestX = keypoint.yx[1]
                if keypoint.yx[0] > highestY: highestY = keypoint.yx[0]
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

        yExpand = ySpread * xFactor * self.__config.GetFaceRectangleYFactor()
        lowestY -= yExpand
        highestY += yExpand

        faceRectangle = ((int(lowestX), int(lowestY)), (int(highestX), int(highestY)))

        return faceRectangle

    
    def __record_person_history(self, detected_objects):
        for object in list(detected_objects):
            object_id = object.object_id
            if object_id in self.__object_history:
                if not object_id in self.__persons_history:
                    self.__persons_history[object_id] = OrderedDict()

                self.__persons_history[object_id][self.__frame_number] = object


    def __people_perception(self, frame):
        poses, _ = self.__pose_engine.DetectPosesInImage(frame)
        bodies = self.__get_qualified_body_detections(poses)
        # for_object_engine = cv2.resize(frame, self.__object_detection_inference_size)
        # objects = self.__pose_engine.detect_with_input_tensor(for_object_engine.flatten())

        detected_objects = []
        for body in bodies:
            body["face_position"] = self.__determine_face_position(body)
            body["has_forehead"] = self.__determine_if_forehead_visible(body)
            body["forehead_center"] = self.__determine_forehead_center(body)
            body["body_rectangle"] = self.__find_body_rectangle(body)
            body["face_rectangle"] = self.__find_face_rectangle(body)

            tracking_info = self.__generate_tracking_info_for_object(frame, body)
            detected_object = DetectedObject()
            detected_object.bounding_box = self.__get_object_bounding_box(body)
            detected_object.tracking_info = tracking_info
            detected_object.body = body
            detected_objects.append(detected_object)

        self.__apply_best_object_matches_to_object_tracking_info(self.__frame_number, detected_objects)
        self.__mark_unmatched_object_ids_as_missing(self.__frame_number)

        self.__process_cleanup_of_missing_objects()

        self.__record_person_history(detected_objects)

        return detected_objects


    def Start(self):
        threading.Thread(target=self.__start_api_server).start()

        while True:
            frame = self.__vs.read()
            counter = 0
            while frame is None:
                if counter == 10:
                    os._exit(1)

                counter += 1
                time.sleep(1)
                frame = vs.read()

            if self.__config.GetFlipVideoFrame():
                frame = cv2.flip(frame, 1)

            self.__frame_number += 1

            self.__add_current_frame_to_rolling_history(frame)

            if self.__do_perception:
                if self.__custom_perception_model is None:
                    detected_objects = self.__people_perception(frame)
                else:
                    for_custom_engine = cv2.resize(frame, self.__custom_model_inference_shape)
                    latency, detected_objects = self.__custom_perception_engine.run_inference(for_custom_engine.flatten())

                self.__data_processor(self.__frame_number, detected_objects)
            else:
                detected_objects = None

            if not self.__frame_processor is None:
                self.__latest_frame = self.__frame_processor(self.__frame_number, frame, detected_objects)
            else:
                self.__latest_frame = frame


    def LoadCustomModel(self, model_path):
        if not self.__custom_engine is None:
            raise Exception("A custom model is already loaded")

        self.__custom_engine = BasicEngine(model_path)

        input_shape = self.__custom_engine.get_input_tensor_shape()
        self.__custom_engine_inference_size = (input_shape[2], input_shape[1])

    
    def RunCustomModel(self, frame):
        if self.__custom_engine is None:
            raise Exception("No custom model is loaded")

        for_custom_engine = cv2.resize(frame, self.__custom_engine_inference_size)
        return self.__custom_engine.run_inference(frame.flatten())


    def GetPersonHistory(self, person_id):
        if not self.__do_perception or not self.__custom_perception_model is None:
            raise Exception("People perception is disabled")
            
        if not person_id in self.__persons_history:
            return None

        return self.__persons_history[person_id]


    def SetConfig(config):
        self.__config = config


    def GetLatestFrame(self):
        return self.__frame_number, self.__latest_frame


if __name__ == "__main__":
    pass