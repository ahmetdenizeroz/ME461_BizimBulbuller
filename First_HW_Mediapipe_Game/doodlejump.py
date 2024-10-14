import cv2
import mediapipe as mp
import numpy as np
import random
import math

# Initialize Mediapipe hand tracking
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Game parameters
screen_width, screen_height = 640, 480
doodle_width, doodle_height = 50, 50
doodle_x = screen_width // 2 - doodle_width // 2
doodle_y = screen_height - doodle_height - 60  
gravity = 0.6
velocity_y = 0
jump_strength = -12 
platform_width, platform_height = 100, 10
scroll_speed = 2
scroll_acceleration = 0.02  # Speed increases 
platform_spacing = 100  # Space between platforms
platforms = [(random.randint(0, screen_width - platform_width), i * platform_spacing) for i in range(5)]
ground_tile = (0, screen_height - 40)  
game_over = False  
game_started = False  
initial_jump_done = False  
score = 0  # score
abc = 0

red = random.randint(0, 255)
green = random.randint(0, 255)
blue = random.randint(0, 255)

red1 = random.randint(0, 255)
green1 = random.randint(0, 255)
blue1 = random.randint(0, 255)

# Set up the video capture
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, screen_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, screen_height)

wafer = cv2.imread("pngegg.png")
size = 50
wafer = cv2.resize(wafer, (size, size))

# Function to calculate distance between two points
def calculate_distance(point1, point2):
    return ((point2.x*screen_width - point1.x*screen_width) ** 2 + (point2.y*screen_height - point1.y*screen_height) ** 2) ** 0.5

# Function to detect if the hand is open
def is_hand_open(hand_landmarks):
    thumb_tip = hand_landmarks.landmark[4]
    index_finger_tip = hand_landmarks.landmark[8]
    middle_finger_tip = hand_landmarks.landmark[12]
    ring_finger_tip = hand_landmarks.landmark[16]
    pinky_finger_tip = hand_landmarks.landmark[20]

    wrist = hand_landmarks.landmark[0]
    
    distance1 = calculate_distance(thumb_tip, index_finger_tip) 
    distance2 = calculate_distance(thumb_tip, wrist)
    distance3 = calculate_distance(index_finger_tip, wrist)
    distance4 = calculate_distance(middle_finger_tip, wrist)
    distance5 = calculate_distance(ring_finger_tip, wrist)
    distance6 = calculate_distance(pinky_finger_tip, wrist)

    #print(distance1, distance2, distance3, distance4, distance5, distance6)

    return (distance1 > 160 and
            distance2 > 150 and
            distance3 > 150 and
            distance4 > 150 and
            distance5 > 150 and
            distance6 > 150)  # Adjust threshold based on testing

# Function to detect peace sign (index and middle finger extended)
def is_peace_sign(hand_landmarks):

    index_finger_tip = hand_landmarks.landmark[8]
    middle_finger_tip = hand_landmarks.landmark[12]
    ring_finger_tip = hand_landmarks.landmark[16]
    pinky_tip = hand_landmarks.landmark[20]
    
    index_knuckle = hand_landmarks.landmark[5]
    middle_knuckle = hand_landmarks.landmark[9]
    ring_knuckle = hand_landmarks.landmark[13]
    pinky_knuckle = hand_landmarks.landmark[17]

    wrist = hand_landmarks.landmark[0]
    
    
    slope_index1 = (index_finger_tip.y*screen_height-index_knuckle.y*screen_height)
    slope_index2 = (index_finger_tip.x*screen_width-index_knuckle.x*screen_width)

    slope_middle1 = (middle_finger_tip.y*screen_height-middle_knuckle.y*screen_height)
    slope_middle2 = (middle_finger_tip.x*screen_width-middle_knuckle.x*screen_width)

    index_angle = abs(math.degrees(math.atan2(slope_index1, slope_index2)))
    middle_angle = abs(math.degrees(math.atan2(slope_middle1, slope_middle2)))
    #print(index_angle)
    #print(middle_angle)
    angle = abs(index_angle-middle_angle)
    # Check if index and middle finger are extended, and ring and pinky are not

    #angle = math.degrees(math.acos(dot / (index_length * middle_length))) 
    #print(angle)
    
    index_to_ring = calculate_distance(index_finger_tip, ring_finger_tip)
    index_to_pinky = calculate_distance(index_finger_tip, pinky_tip)
    wrist_to_ring = calculate_distance(wrist, ring_finger_tip)
    wrist_to_pinky = calculate_distance(wrist, pinky_tip)
    wrist_to_middle = calculate_distance(wrist, middle_finger_tip)

    return (index_to_ring > 150 and
            index_to_pinky > 150 and
            wrist_to_ring < 150 and
            wrist_to_pinky < 150 and
            wrist_to_middle > 150 and
            angle > 20 or angle < -20)

# Function to draw doodle
def draw_doodle(frame, x, y):
    cv2.circle(frame, (x + int(doodle_width/2), y + int(doodle_height/2)), 25, (255, 0, 0), -1)
    for i in range(0, 50, 5):
        cv2.rectangle(frame, (x+i, y+i), (x+i+5, y+i+5), (red1, blue1, green1), -1)

# Function to draw platforms
def draw_platforms(frame, platforms):
    for plat in platforms:
        plat_x, plat_y = plat
        top_left = (int(plat_x), int(plat_y))
        bottom_right = (int(plat_x + platform_width), int(plat_y + platform_height))
        cv2.rectangle(frame, top_left, bottom_right, (red, green, blue), -1)

# Function to draw the ground tile
def draw_ground_tile(frame):
    cv2.rectangle(frame, ground_tile, (screen_width, ground_tile[1] + platform_height), (0, 255, 0), -1)

# Function to show Game Over message
def display_game_over(frame):
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, "PEACE TO RESTART", (screen_width // 2 - 200, screen_height // 2), font, 1, (0, 0, 255), 3)

    cv2.rectangle(frame, ground_tile, (screen_width, ground_tile[1] + platform_height), (0, 255, 0), -1)

# Function to show Game Start message
def display_start_message(frame):
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, "OPEN HAND TO START", (screen_width // 2 - 200, screen_height // 2), font, 1, (255, 255, 255), 2)

# Function to display score
def display_score(frame, score):
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, f"Score: {score}", (10, 30), font, 1, (255, 255, 255), 2)

# Function to reset the game state for restart
def reset_game():
    global platforms, doodle_y, velocity_y, score, scroll_speed, game_over, game_started, initial_jump_done, gravity, jump_strength
    platforms = [(random.randint(0, screen_width - platform_width), i * platform_spacing) for i in range(5)]
    doodle_y = ground_tile[1] - doodle_height  # Reset doodle position
    velocity_y = 0  # Reset velocity
    score = 0  # Reset score
    scroll_speed = 2  # Reset scroll speed
    gravity = 0.6
    jump_strength = -12
    game_over = False  # Game is no longer over
    game_started = False  # Wait for user to start the game
    initial_jump_done = False  # Reset initial jump flag

# Main game loop
while True:
    ret, frame = cap.read()
    if not ret:
        break
    if abc == 5:
        
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)
        
        red1 = random.randint(0, 255)
        green1 = random.randint(0, 255)
        blue1 = random.randint(0, 255)
        abc = 0

    #im2gray = cv2.cvtColor(wafer, cv2.COLOR_BGR2GRAY)
    #ret, mask = cv2.threshold(im2gray, 1, 255, cv2.THRESH_BINARY)

    frame = cv2.flip(frame, 1) 
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Drawing Hand Landmarks
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Get x-coordinate of the index finger
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            doodle_x = int(index_finger_tip.x * screen_width) - doodle_width // 2
            
            # Detect if hand is open to start the game
            
            if is_hand_open(hand_landmarks):
                if not game_started and not game_over:
                    game_started = True
                    doodle_y = ground_tile[1] - doodle_height  # Start on the ground tile
                    velocity_y = jump_strength  # Trigger the initial jump
                    initial_jump_done = True
                    score = 0  # Reset score when starting a new game
                    scroll_speed = 2  # Reset scroll speed

            # Detect peace sign for restart after game over

            print(is_peace_sign(hand_landmarks))
            #print(is_hand_open(hand_landmarks))

            if game_over and is_peace_sign(hand_landmarks):
                print("bir")
                reset_game()  # Reset all game parameters

    if game_started:
        doodle_y += int(velocity_y)
        velocity_y += gravity

        on_platform = False
        for plat in platforms:
            plat_x, plat_y = plat
            if (doodle_y + doodle_height >= plat_y and
                doodle_y + doodle_height <= plat_y + platform_height and
                doodle_x + doodle_width > plat_x and 
                doodle_x < plat_x + platform_width and
                velocity_y >= 0):
                velocity_y = jump_strength  # Make the doodle jump again
                score += 10  # Increment score for each jump
                scroll_speed += scroll_acceleration  # Increase speed slightly after each jump
                on_platform = True
                break

        if doodle_y + doodle_height >= ground_tile[1] and initial_jump_done and not on_platform:
            game_over = True  # End the game
            print("iki")
            display_game_over(frame)

        scroll_speed += scroll_acceleration
        #velocity_y += scroll_acceleration
        gravity += 0.0065
        jump_strength -= 0.005
       
        platforms = [(plat[0], plat[1] + scroll_speed) for plat in platforms]
        if platforms[-1][1] >=platform_spacing:
            new_platform = (random.randint(0, screen_width - platform_width), -platform_height)
            platforms.append(new_platform)

        platforms = [plat for plat in platforms if plat[1] < screen_height]

    draw_ground_tile(frame)
    draw_doodle(frame, doodle_x, doodle_y)
    draw_platforms(frame, platforms)
    display_score(frame, score)
   
    abc += 1

    #print(doodle_x)
    #print(doodle_y)


    # Last Unsolver part, comment below three line for code to work without wafer!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #roi = frame[doodle_x:size+doodle_x, doodle_y:size+doodle_y]
    #roi[np.where(mask)] = 0
    #roi += wafer

    if not game_started and not game_over:
        display_start_message(frame)

    cv2.imshow('Doodle Jump', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
hands.close()
