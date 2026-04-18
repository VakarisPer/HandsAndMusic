import mediapipe as mp
import cv2
import HelperFunctions as help
import HandGesture as hg


capture = cv2.VideoCapture(0)

#https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
#https://docs.opencv.org/3.4/db/deb/tutorial_display_image.html

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

with mp_hands.Hands(min_detection_confidence=0.6, min_tracking_confidence=0.6) as hands:
    while capture.isOpened():
        ret, frame = capture.read()
        if(ret == False):
            break
        frame = cv2.flip(frame, 1) # numbers: 0: horizontal, 1: vertical, -1: both
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        detected_image = hands.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) 

        if detected_image.multi_hand_landmarks:
            for hand_lms in detected_image.multi_hand_landmarks:
                mp_drawing.draw_landmarks(image, hand_lms,
                    mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(
                        color=(255, 0, 255), thickness=2, circle_radius=2),
                    connection_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(
                        color=(20, 180, 90), thickness=2, circle_radius=2)
                    )
                
                h,w,_ = image.shape

                #thumb tip is 4, index tip is 8, middle tip is 12, ring tip is 16, pinky tip is 20

                thumb = hand_lms.landmark[4]
                index = hand_lms.landmark[8]
                distante = help.get_pixel_distance(thumb, index, w, h)

                if distante < 30:
                    print("collision")
                    cv2.putText(image, "KIMBA", (200,200), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 255, 0),2)

                gesture_name, gesture_score = hg.recognize_hand_gesture(hand_lms)
                cv2.putText(image, f"Gesture: {gesture_name} ({gesture_score:.1f})", (50, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

                cv2.circle(image, (int(hand_lms.landmark[4].x * w), int(hand_lms.landmark[4].y * h)), 10, (255, 0, 255), -1)
                cv2.circle(image, (int(hand_lms.landmark[8].x * w), int(hand_lms.landmark[8].y * h)), 10, (255, 0, 255), -1)
                
                    
        cv2.imshow('Webcam', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        
capture.release()
cv2.destroyAllWindows()