import ball
import cv2
import mediapipe as mp
import random


# Variables
w = 2000
h = 1200
target_pos = (random.randint(int(w/20), int(19*w/20)),random.randint(int(w/20), int(h - w/20)))
#target_pos = (int(w/2) ,int(h/2))
is_target_hit = False
point = 0
font = cv2.FONT_HERSHEY_SIMPLEX
is_hit = False

is_hit_left = False
is_hit_right = False
is_hit_bottom = False
is_hit_top = False

# Functions
def distance(point1, point2):
    length = ((point2[0]-point1[0])**2 + (point2[1]-point1[1])**2)**0.5
    vector = (point2[0] - point1[0], point2[1] - point1[1])
    return length, vector

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Video Capture
capture = cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

ball = ball.ball((90,90,90), int(w/40), (int(w/2), int(h/2)), (40, 40))


with mp_hands.Hands(min_detection_confidence = 0.2, min_tracking_confidence = 0.2) as hands:
    while capture.isOpened():
        ret, frame = capture.read()
        frame = cv2.resize(frame, (w, h))
        if not ret:
            print("Check your Webcam")
            break

        # frame flip
        frame = cv2.flip(frame, 1)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(rgb_frame)

	    #Ball Drawing
        ball.move()
        cv2.circle(frame, ball.position, ball.size, ball.color, -1)

        #target

        cv2.circle(frame, target_pos,int(w/20),(255,46,175),-1)


        if results.multi_hand_landmarks:
            print(type(results.multi_hand_landmarks))
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS, mp_drawing.DrawingSpec(color = (111, 111, 111), thickness = 2), mp_drawing.DrawingSpec(color = (5, 5, 5), thickness = 2))
                
            wrist1 = results.multi_hand_landmarks[0].landmark[0]
            knuckle11 = results.multi_hand_landmarks[0].landmark[5]
            knuckle41 = results.multi_hand_landmarks[0].landmark[17] 
            point1 = (int((knuckle11.x * w * 2+ wrist1.x * w+ knuckle41.x * w*2)/5), int((knuckle11.y * h * 2+ wrist1.y * h+ knuckle41.y * h*2)/5))

            if len(results.multi_hand_landmarks) > 1:
                wrist2 = results.multi_hand_landmarks[1].landmark[0]
                knuckle12 = results.multi_hand_landmarks[1].landmark[5]
                knuckle42 = results.multi_hand_landmarks[1].landmark[17]
                point2 = (int((knuckle12.x * w * 2+ wrist2.x * w+ knuckle42.x * w*2)/5), int((knuckle12.y * h * 2+ wrist2.y * h+ knuckle42.y * h*2)/5)) 

                if distance(point2, point1)[0] < w/4:
                    cv2.line(frame, point1, point2, (5,255,46), 5)

                    dx = (point1[0]-point2[0]) / distance(point2, point1)[0]
                    dy = (point1[1]-point2[1]) / distance(point2, point1)[0]

                    midpoint = ((point1[0]+point2[0])/2, (point1[1]+point2[1])/2)

                    if distance(midpoint, ball.position)[0] < distance(point2, point1)[0]/2:
                        normal_dist = distance(midpoint, ball.position)[1][0]*-dy + distance(midpoint, ball.position)[1][1] * dx
                        if abs(normal_dist) -ball.size < 1 and not is_hit:
                            ball.Change_Dir((dx, dy))
                            is_hit = True
                        if abs(normal_dist) -ball.size > 1:
                            is_hit = False
        
        
        
        if ball.position[0] - ball.size < 1 and not is_hit_left: 
            ball.Change_Dir((0, 1))
            is_hit_left = True
        else:
            is_hit_left = False

        if ball.position[0] + ball.size > w - 1 and not is_hit_right:
            ball.Change_Dir((0, 1))
            is_hit_right = True
        else:
            is_hit_right = False

        if ball.position[1] -ball.size < 1 and not is_hit_top:
            ball.Change_Dir((1, 0))
            is_hit_top = True
        else:
            is_hit_top = False

        if ball.position[1] + ball.size > h - 1  and not is_hit_bottom:
            ball.Change_Dir((1,0))
            is_hit_bottom = True
        else:
            is_hit_bottom = False

        if distance(target_pos, ball.position)[0] < w/20 and not is_target_hit:
            point += 10
            is_target_hit = True

        if distance(target_pos, ball.position)[0] > w/20:
            is_target_hit = False
        
        cv2.putText(frame, f"Score: {point}", (10, 30), font, 1, (255, 255, 255), 2)

        #print(point)
        #print(ball.velocity)
        #print(ball.position)
        cv2.imshow("Game", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

capture.release()
cv2.destroyAllWindows()

