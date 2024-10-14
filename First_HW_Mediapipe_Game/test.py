import cv2
import mediapipe as mp
import numpy as np
import random

# Initialize MediaPipe components for hand detection
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Start capturing video from the webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920) 
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080) 

acc = 0.5

#Fruit Ninja
circle_radius = 30
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
circles = []
dead_circle = []


def create_circle():
    x = random.randint(circle_radius, 1280 - circle_radius)
    y = 720 + circle_radius  # Start from below the screen
    color = random.choice(colors)
    speed = random.uniform(20, 25)  # Random speed for each circle
    return {'x': x, 'y': y, 'color': color, 'speed': speed}

for _ in range(3):
    circles.append(create_circle())

# Initialize the Hands model
with mp_hands.Hands(min_detection_confidence=0.4, min_tracking_confidence=0.4) as hands:

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            break

        # Flip the frame horizontally for a later selfie-view display
        frame = cv2.flip(frame, 1)

        # Convert the BGR frame to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the image and get hand landmarks
        results = hands.process(rgb_frame)
        

        # Draw hand landmarks
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                for idx, landmark in enumerate(hand_landmarks.landmark):
                    h, w, _ = frame.shape
                    #print(                    #print(w)
                    x, y = int(landmark.x * w), int(landmark.y * h)

                    # Draw the index number of the landmark
                    cv2.putText(frame, str(idx), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                # Draw landmarks and connections
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS, mp_drawing.DrawingSpec(color=(255,255,0), thickness=2), mp_drawing.DrawingSpec(color=(12,15,16), thickness=2))

                # Get landmark coordinates
                wrist = hand_landmarks.landmark[0]   # Thumb tip
                knuckle1 = hand_landmarks.landmark[5]   # Index finger tip
                knuckle2 = hand_landmarks.landmark[9]  # Middle finger tip
                knuckle3 = hand_landmarks.landmark[13]    # Ring finger tip
                knuckle4 = hand_landmarks.landmark[17]   # Pinky finger tip
                mid = hand_landmarks.landmark[10]

                point1 = (int((knuckle1.x * 1280 * 2+ wrist.x * 1280+ mid.x * 1280*2)/5), int((knuckle1.y * 720 * 2+ wrist.y * 720+ mid.y * 720*2)/5))
                point2 = (int((knuckle4.x * 1280 * 2+ wrist.x * 1280+ mid.x * 1280*2)/5), int((knuckle4.y * 720 * 2+ wrist.y * 720+ mid.y * 720*2)/5))
		
                length = ((point2[0]-point1[0])**2 + (point2[1]-point1[1])**2) ** 0.5
                dx = (point1[0]-point2[0]) / length
                dy = (point1[1]-point2[1]) / length

                point3 = (int(point2[0] + 300*dx), int(point2[1] + 300*dy))
                
                distance1 = hand_landmarks.landmark[4]
                distance2 = hand_landmarks.landmark[6]

                distance = (int(((distance2.x - distance1.x)*1280))**2 + (int((distance2.y - distance1.y)*720))**2)**0.5
                
                if distance < 100:
                    cv2.line(frame, point2, point3, (159, 142, 25), 10) 
# Ninja
                for circle in circles:
                    circle['y'] -= circle['speed']  # Move circle upwards
# Draw the circle
                    cv2.circle(frame, (int(circle['x']), int(circle['y'])), circle_radius, circle['color'], -1)
# If the circle goes off the screen, reset it to below
                    
                    #if circle['y'] < 360:
                    #    circle['speed'] = -circle['speed']

                    destroy_cond = ((point3[0]-circle['x'])**2+(point3[1]-circle['y'])**2)**0.5 
                    
                    circle["speed"] -= acc

                    if destroy_cond < 30:
                        dead_circle.append(circle)
                        circles.remove(circle)
                        circles.append(create_circle())

        # Display the frame
        cv2.imshow('Hand Landmark Detection', frame)

        # Exit the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Release the video capture and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()
