import cv2
import imutils
import numpy as np
from scipy.spatial import distance as dist
from imutils.video import FileVideoStream
from imutils.video import VideoStream
from imutils import face_utils
from datetime import datetime
from multithreadedPerimeter import MultithreadedPerimeter
from processManager import ProcessManager
from gesture import Gesture
from handGestureDetector import HandGestureDetector
from blinkDetector import BlinkDetector

class GestureDetector():
    def __init__(self):
        # Next value not being used right now, but may be in the near future.
        # self.is_black_and_white = False

        self.process_manager = ProcessManager()
        self.hand_gesture_detector = HandGestureDetector()
        self.blink_detector = BlinkDetector()

        self.fist_event = None
        self.palm_event = None
        self.blink_event = None
        self.gesture_detected = None

    def on_fist(self, callback):
        self.fist_event = callback

    def on_palm(self, callback):
        self.palm_event = callback

    def on_blink(self, callback):
        self.blink_event = callback

    def get_gesture_detected(self):
        return self.gesture_detected

    # Method is to be run in separate thread
    def detect(self, frame, timestamp, open_eye_threshold, fist_perimeter, palm_perimeter, left_eye_perimeter, right_eye_perimeter):

        # Code we may use in the future for contrast
        '''
        panel = np.zeros([100, 700], np.uint8)

        hContrastRed = 0
        lContrastRed = 170

        low_contrast = np.array([hContrastRed, hContrastGreen, hContrastBlue])
        high_contrast = np.array([lContrastRed, lContrastGreen, lContrastBlue])

        mask = cv2.inRange(frame, low_contrast, high_contrast)
        mask_inv = cv2.bitwise_not(mask)

        color_frame = cv2.bitwise_and(frame, frame, mask=mask_inv)
        gray_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGR2GRAY)

        if self.is_black_and_white:
            current_frame = gray_frame
        else:
            current_frame = frame
        '''

        current_frame = frame

        # Creating two grandchild processes (relative to main.py)
        # First (hand_gesture) will create two more sub-processes while blink will not
        self.process_manager.add_process(
                self.hand_gesture_detector.detect, (current_frame, fist_perimeter, palm_perimeter))
        self.process_manager.add_process(
                self.blink_detector.detect, (current_frame, left_eye_perimeter, right_eye_perimeter))

        # Wait for children to yield control back to this process
        self.process_manager.on_done()

    def trigger_events(self, timestamp, open_eye_threshold, fist_perimeter, palm_perimeter, left_eye_perimeter, right_eye_perimeter):

        self.gesture_detected = None
        if fist_perimeter.is_set():
            self.gesture_detected = "fist"
            self.fist_event(timestamp)

        if palm_perimeter.is_set():
            self.gesture_detected = "palm"
            self.palm_event(timestamp)
        
        if left_eye_perimeter.is_set() and right_eye_perimeter.is_set():
            if open_eye_threshold / 100 > (left_eye_perimeter.get_ratio() + right_eye_perimeter.get_ratio()) / 2:
                self.gesture_detected = "blink"
                self.blink_event(timestamp)

    ''' This code is NOT being used right now 
    # Used for creating contrast within the frame to detect hand gestures more clearly
    def set_frame_contrast(Red, Green, Blue):
        redContrast = Red
        greenContrast = Green
        blueContrast = Blue
        return [redContrast, greenContrast, blueContrast]

    def get_gray_hand_frame(self, hand_frame):
        low_contrast = np.array(GestureDetector.set_frame_contrast(0, 0, 0))
        high_contrast = np.array(
                GestureDetector.set_frame_contrast(132, 255, 255))

        return GestureDetector.changing_hand_frame(
                self, hand_frame, low_contrast, high_contrast)

    def changing_hand_frame(self, frame, low_cont, high_cont):
        mask = cv2.inRange(frame, low_cont, high_cont)
        mask_inv = cv2.bitwise_not(mask)
        color_frame = cv2.bitwise_and(frame, frame, mask=mask_inv)
        gray_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGR2GRAY)
        return gray_frame

    def get_cropped_hand_frame(frame):
       return imutils.resize(frame, width=800)

    def detect_fist_or_palm(self, frame):
        fist_cascade = cv2.CascadeClassifier('fist.xml')
        palm_cascade = cv2.CascadeClassifier('palm.xml')
        self.fist = fist_cascade.detectMultiScale(frame, 1.3, 5)
        self.palm = palm_cascade.detectMultiScale(frame, 1.3, 5)

        if len(self.fist) > 0:
            self.has_made_fist = True
        if len(self.palm) > 0:
            self.has_made_palm = True

        for (x, y, w, h) in self.fist:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
        for (x, y, w, h) in self.palm:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)

    def start(self):
        self.timer.on_time(self.on_tick)

        self.source = VideoStream(src=0).start()

        while True:

            blink_frame = self.source.read()
            cropped_blink_frame = imutils.resize(self.source.read(), width=800)
            gray = cv2.cvtColor(cropped_blink_frame, cv2.COLOR_BGR2GRAY)

            # detect faces in the grayscale blink_frame
            rects = self.detector(gray, 0)

            # loop over the face detections
            for rect in rects:

                shape = self.predictor(gray, rect)
                leftEye, rightEye = GestureDetector.convert_facial_landmark(
                    self, shape, rect, gray)
                # average the eye aspect ratio together for both eyes
                GestureDetector.set_ears(
                    self, leftEye, rightEye)
                GestureDetector.visualize_eyes(
                    self, leftEye, rightEye, cropped_blink_frame)
                GestureDetector.check_eye_aspect_ratio(
                    self, self.ear, self.ear_thresh, self.ear_consec_frame)
                GestureDetector.make_frame_labels(self, blink_frame)
                GestureDetector.set_cropped_face_frame(
                    self, rects, cropped_blink_frame, gray)

            hand_frame = self.source.read()
            low_contrast = np.array(GestureDetector.set_frame_contrast(0, 0, 0))
            high_contrast = np.array(
                GestureDetector.set_frame_contrast(90, 255, 255))

            gray_frame = GestureDetector.changing_hand_frame(
                self, hand_frame, low_contrast, high_contrast)

            GestureDetector.detect_fist_or_palm(self, gray_frame)

            cv2.imshow("Blink Frame", blink_frame)
            cv2.imshow('Hand Gesture Frame', gray_frame)

    def eye_aspect_ratio(eye):
        # compute the euclidean distances between the two sets of
        # vertical eye landmarks (x, y)-coordinates
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])

        # compute the euclidean distance between the horizontal
        # eye landmark (x, y)-coordinates
        C = dist.euclidean(eye[0], eye[3])

        # compute the eye aspect ratio
        return (A + B) / (2.0 * C)

    def get_gray_blink_frame(cropped_blink_frame):
        return cv2.cvtColor(cropped_blink_frame, cv2.COLOR_BGR2GRAY) 
        '''