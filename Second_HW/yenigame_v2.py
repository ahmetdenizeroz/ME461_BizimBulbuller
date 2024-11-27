import pygame
import cv2
import mediapipe as mp
import random
import numpy as np

# Initialize Pygame
pygame.init()
screen_width, screen_height = pygame.display.Info().current_w, pygame.display.Info().current_h
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()

# Initialize MediaPipe for hand tracking
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2)
cap = cv2.VideoCapture(0)  # Open webcam

# Tile class
class Tile:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width // 10  # 1/10 of screen width
        self.height = 20
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.rect = pygame.Rect(0, screen_height - 100, self.width, self.height)
        self.randomize_position()

    def randomize_position(self):
        # Randomize position anywhere within the screen
        self.rect.x = random.randint(0, self.screen_width - self.width)
        self.rect.y = random.randint(0, self.screen_height - self.height)

    def draw(self, screen):
        # Draw the tile on the screen
        pygame.draw.rect(screen, (0, 255, 0), self.rect)

# Ball class
class Ball:
    def __init__(self, x, y, radius, speed):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.direction = np.array([random.choice([-1, 1]), random.choice([-1, 1])])

    def update(self):
        # Update ball position
        self.x += self.direction[0] * self.speed
        self.y += self.direction[1] * self.speed

        # Reflect from screen borders
        if self.x - self.radius <= 0 or self.x + self.radius >= screen_width:
            self.reflect_from_normal(np.array([1, 0]))  # Reflect horizontally
        if self.y - self.radius <= 0 or self.y + self.radius >= screen_height:
            self.reflect_from_normal(np.array([0, 1]))  # Reflect vertically

    def reflect_from_normal(self, normal):
        # Calculate reflection vector: R = I - 2 * (I . N) * N
        self.direction = self.direction - 2 * np.dot(self.direction, normal) * normal

    def reflect_from_line(self, line_start, line_end):
        # Create a vector representing the line between hands
        line_vector = np.array(line_end) - np.array(line_start)
        line_vector = line_vector / np.linalg.norm(line_vector)  # Normalize the vector

        # Normal vector perpendicular to the line
        normal = np.array([-line_vector[1], line_vector[0]])

        # Get vector from ball to closest point on line
        ball_to_line_start = np.array([self.x, self.y]) - np.array(line_start)
        projection_length = np.dot(ball_to_line_start, line_vector)
        closest_point_on_line = np.array(line_start) + projection_length * line_vector

        # Check if the ball is close enough to the line to reflect
        if np.linalg.norm([self.x - closest_point_on_line[0], self.y - closest_point_on_line[1]]) <= self.radius:
            self.reflect_from_normal(normal)

    def draw(self, screen):
        # Draw the ball on the screen
        pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), self.radius)

# Initialize the tile and the ball
tile = Tile(screen_width, screen_height)
ball = Ball(screen_width // 2, screen_height // 2, screen_width // 80, 15)

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
    
    screen.fill((0,0,0))

    # Capture frame from webcam and process it
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame horizontally for a mirrored view and convert to RGB
    frame_rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)

    # Process the frame using MediaPipe to detect hands
    results = hands.process(frame_rgb)

    # Get hand landmarks (index finger tips) if hands are detected
    left_hand = None
    right_hand = None

    if results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            hand_label = results.multi_handedness[idx].classification[0].label
            # Get the index finger tip coordinates
            if hand_label == "Left":
                left_hand = (int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x * screen_width),
                             int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y * screen_height))
            elif hand_label == "Right":
                right_hand = (int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x * screen_width),
                              int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y * screen_height))

    # Fill the screen with black (or any background color)
    screen.fill((0, 0, 0))

    # Draw hand landmark connections (for visualization only)
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            for connection in mp_hands.HAND_CONNECTIONS:
                start_idx, end_idx = connection
                start = hand_landmarks.landmark[start_idx]
                end = hand_landmarks.landmark[end_idx]

                # Convert normalized coordinates to screen space
                start_pos = (int(start.x * screen_width), int(start.y * screen_height))
                end_pos = (int(end.x * screen_width), int(end.y * screen_height))

                # Draw a line between the start and end positions (no reflection from these lines)
                pygame.draw.line(screen, (255, 255, 255), start_pos, end_pos, 2)

    # Draw the tile
    tile.draw(screen)

    # Move and update the ball
    ball.update()

    # Reflect the ball if it hits the tile
    if tile.rect.colliderect(pygame.Rect(ball.x - ball.radius, ball.y - ball.radius, ball.radius * 2, ball.radius * 2)):
        tile.randomize_position()  # Change tile position when the ball hits it
        ball.reflect_from_normal(np.array([0, 1]))  # Reflect with respect to a horizontal surface

    # Draw the ball
    ball.draw(screen)

    # Draw the line between hands if both are detected and reflect ball from it
    if left_hand and right_hand:
        # Calculate the distance between the two hands
        distance = np.linalg.norm(np.array(left_hand) - np.array(right_hand))

        # Constrain the line to be a maximum of 1/4 the screen width
        max_distance = screen_width // 4
        if distance <= max_distance:
            # Draw the red line between the two index fingers (reflection happens only here)
            pygame.draw.line(screen, (255, 0, 0), left_hand, right_hand, 10)

            # Reflect the ball only from this specific red line
            ball.reflect_from_line(left_hand, right_hand)

    # Update the display
    pygame.display.flip()

    # Control the frame rate
    clock.tick(60)

# Release resources
cap.release()
pygame.quit()

