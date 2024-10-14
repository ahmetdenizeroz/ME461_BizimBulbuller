import ball
import cv2
import mediapipe as mp

# Variables
w = 1280
h = 720

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Video Capture
capture = cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, w)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

ball = ball.ball((90,90,90), 20, (int(w/2), int(h/2)), (20, 20))

with mp_hands.Hands(min_detection_confidence = 0.4, min_tracking_confidence = 0.4) as hands:
    while capture.isOpened():
        ret, frame = capture.read()
        if not ret:
            print("Chack your Webcam")
            break

        # frame flip
        frame = cv2.flip(frame, 1)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS, mp_drawing.DrawingSpec(color = (111, 111, 111), thickness = 2), mp_drawing.DrawingSpec(color = (5, 5, 5), thickness = 2))
       
        ball.move()

        if ball.position[0] < 10: 
            ball.Change_Dir((0, 1))
        if ball.position[0] > 1270:
            ball.Change_Dir((0, -1))

        if ball.position[1] < 10:
            ball.Change_Dir((-1, 0))
        if ball.position[1] > 710:
            ball.Change_Dir((1,0))
        print(ball.velocity)
        print(ball.position)
        cv2.circle(frame, ball.position, ball.size, ball.color, -1)

        cv2.imshow("Game", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

capture.release()
cv2.destroyAllWindows()

