import mediapipe as mp
import cv2 as cv

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Video Capture 
capture = cv.VideoCapture(0)

with mp_hands.Hands() as hands:
    while capture.isOpened():
        ret, frame = capture.read()
        if not ret:
            print("Failed to capture image!")
            break
        frame = cv.flip(frame, 1)
        rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS, mp_drawing.DrawingSpec(color=(255,255,0), thickness=2), mp_drawing.DrawingSpec(color=(12,15,16), thickness = 2))
        cv.imshow("Fruit Ninja", frame)
        if cv.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
cv.destroyAllWindows()
