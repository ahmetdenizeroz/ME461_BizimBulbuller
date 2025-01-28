from neopixel import Neopixel
import array, time
from machine import Pin, PWM, ADC
import utime

# Constants
RED = (255, 0, 0)
DEBOUNCE_TIME = 50
DOUBLE_CLICK_TIME = 300  # Time in milliseconds for a double click

# Pins and settings
POT = ADC(26)
NUMPIX = 10
STRIP = Neopixel(NUMPIX, 0, 28, "RGB")
RESET_BUTTON_PIN = 16
LEFT_BUTTON_PIN = 14
RIGHT_BUTTON_PIN = 22

# Variables
delay = 0.5
ball_position = NUMPIX - 1
ball_direction = -1
ball_speed = 0.2  # Initial speed in seconds
points = 0
start_time = 0

game_running_single = False
game_stop = True

stopper = 0
stop = False

# Multiplayer settings
is_left = False
is_right = False
is_left_ready = False
is_right_ready = False
left_point = 0
right_point = 0

# UART setup
UART = machine.UART(0, baudrate=9600, tx=machine.Pin(12), rx=machine.Pin(13))

# Debouncing Variables
left_last_press_time = 0
right_last_press_time = 0
reset_last_press_time = 0


# Interrupt-based button handlers
def left_button_handler(pin):
    global delay, left_last_press_time
    current_press_time = time.ticks_ms()
    if time.ticks_diff(current_press_time, left_last_press_time) > DEBOUNCE_TIME:
        print("Left button pressed")
        delay = min(delay + 0.1, 2.0)  # Increment delay with a max limit
        left_last_press_time = current_press_time

def right_button_handler(pin):
    global delay, right_last_press_time, stop
    current_press_time = time.ticks_ms()
    
    if time.ticks_diff(current_press_time, right_last_press_time) > DEBOUNCE_TIME and time.ticks_diff(current_press_time, right_last_press_time) < DOUBLE_CLICK_TIME:
        if stop:
            stop = False
        elif not stop:
            stop = True
            print("Game is Stopped")
        print(stop)
        right_last_press_time = current_press_time

    if time.ticks_diff(current_press_time, right_last_press_time) > DOUBLE_CLICK_TIME:
        print("Right button pressed")
        delay = max(delay - 0.1, 0.1)  # Decrement delay with a min limit
        right_last_press_time = current_press_time

def button_handler(pin):
    global reset_last_press_time 
    current_press_time = time.ticks_ms()
    if time.ticks_diff(current_press_time, reset_last_press_time) > DEBOUNCE_TIME:
        reset_last_press_time = current_press_time
        machine.soft_reseet()
        
def multi_game_starter(pin):
    global delay, left_last_press_time
    current_press_time = time.ticks_ms()
    if time.ticks_diff(current_press_time, left_last_press_time) > DEBOUNCE_TIME:
        print("Start Button is pressed")
        game_stop = False
        left_last_press_time = current_press_time

def game_starter(pin):
    global delay, left_last_press_time, game_stop
    current_press_time = time.ticks_ms()
    if time.ticks_diff(current_press_time, left_last_press_time) > DEBOUNCE_TIME:
        if not game_running_single:
            print("Start Button is pressed")            
            game_stop = False
            left_last_press_time = current_press_time
            
def multi_left_choose(pin):
    global delay, left_last_press_time, is_left, is_right, is_left_ready, UART
    current_press_time = time.ticks_ms()
    if time.ticks_diff(current_press_time, left_last_press_time) > DEBOUNCE_TIME:
        if is_left and not is_left_ready:
            print("Left side is ready")
            UART.write("v")
            is_left_ready = True
            
            left_last_press_time = current_press_time
        if not is_left and not is_right:
            print("Left side is choosen")
            is_left = True
            UART.write("l")
            left_last_press_time = current_press_time
            
def multi_right_choose(pin):
    global delay, right_last_press_time, is_right, is_left, is_right_ready, UART
    current_press_time = time.ticks_ms()
    if time.ticks_diff(current_press_time, right_last_press_time) > DEBOUNCE_TIME:
        if is_right and not is_right_ready:
            print("Right side is ready")            
            is_right_ready = True
            UART.write("b")
            right_last_press_time = current_press_time
        if not is_left and not is_right:
            print("Right side is choosen")            
            is_right = True
            UART.write("r")
            right_last_press_time = current_press_time

# Setup buttons
left_button = Pin(LEFT_BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
right_button = Pin(RIGHT_BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
reset_button = Pin(RESET_BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)

# Utility functions
def ByteDisplay(val):
    """Displays a byte value on the LEDs."""
    
    left_button.irq(trigger=Pin.IRQ_FALLING, handler=left_button_handler)
    right_button.irq(trigger=Pin.IRQ_FALLING, handler=right_button_handler)
    reset_button.irq(trigger=Pin.IRQ_RISING, handler=button_handler)
    
    num = bin(val)[2:]
    binary = '0' * (8 - len(num)) + num  # Convert value to binary representation
    print("Current number:", val)
    print("Binary representation:", binary)
    for i in range(1, 9):
        STRIP.set_pixel(i, (int(binary[8 - i]) * 255, 0, 0))
    STRIP.show()
    utime.sleep(delay)
    STRIP.fill((0, 0, 0))
    print('Delay between numbers is:', delay)
    while stop:
        a = 7

def PotRead():
    """Reads the potentiometer value."""
    current_value = POT.read_u16()
    utime.sleep(0.05)
    next_value = POT.read_u16()
    return next_value - current_value

def clear_leds():
    """Clears all LEDs."""
    for i in range(NUMPIX):
        STRIP.set_pixel(i, (0, 0, 0))
    STRIP.show()

def update_leds(position):
    """Updates the LEDs based on the ball position."""
    clear_leds()
    STRIP.set_pixel(position, (0, 255, 0))
    STRIP.show()

def game_summary():
    """Displays a game over sequence on the LEDs."""
    clear_leds()
    for i in range(NUMPIX):
        STRIP.set_pixel(i, (255, 0, 0))
        STRIP.show()
        utime.sleep(0.1)
    clear_leds()

def orchestrate():
    """Prompts the user for game mode selection."""
    
    
    
    return input(
        """
        Welcome! Please enter the corresponding number:
        1: Binary Counter
        2: LED Pong Single Player
        3: Potentiometer Data
        4: LED Pong Two Player
        Selection: """)

# Main loop
while True:
    selection = orchestrate()
    if selection == '1':
        try:
            for i in range(0, 255):
                k = i % 256 
                ByteDisplay(k)
        except KeyboardInterrupt:
            a = 6
    if selection == '2':
        left_button.irq(trigger=Pin.IRQ_FALLING, handler=game_starter)
        while True:
            if not game_running_single and not game_stop:
                print("Game starting! Get ready!")
                game_running_single = True
                start_time = time.time()
                ball_position = NUMPIX-1
                ball_direction = -1
                ball_speed = 0.2
                points = 0
    
            if game_running_single:
                elapsed = time.time() - start_time
                if elapsed >= 60:
                    print(f"Game Over! Total Points: {points}")
                    game_summary()
                    game_running_single = False
                    game_stop = True
                    print("Press the button to restart.")
                    continue
        
            # Ball movement
                ball_position += ball_direction
                update_leds(ball_position)
                time.sleep(ball_speed)
                if ball_position == 0 or ball_position == NUMPIX-1:
                    ball_direction *= -1  # Bounce
                    if ball_position == 0:
                        print("Ball missed! -10 points.")
                        points -= 10
                        ball_speed = 0.2  # Reset speed

            
                # POT interaction during last LEDs
                if ball_position < 2 and ball_direction == -1:
                    twist = PotRead()
                    if twist > 500 or twist < -500:
                        print(f"Ball hit! +{twist // 100} points.")
                        points += twist // 100
                        ball_direction *= -1
                        ball_speed = max(0.05, 0.2 - abs(twist) / 10000)
                    else:
                        print("Missed opportunity to hit!")
            
    if selection == '3':
        while True:
            print(PotRead())
            
    if selection == '4':
        left_button.irq(trigger=Pin.IRQ_FALLING, handler=multi_left_choose)
        right_button.irq(trigger=Pin.IRQ_FALLING, handler=multi_right_choose)
        
        game_area = NUMPIX*2
        
        while True:
            #UART.write("boo") 
            #ball starts from left side.
            if is_left and is_left_ready and is_right_ready and not game_running_single:
                print("Game starting! Get ready!!")
                game_running_single = True
                start_time = time.time()
                ball_position = 0
                ball_direction = 1
                ball_speed = 0.2
                left_point = 0
            elif is_right and is_right_ready and is_left_ready and not game_running_single:
                print("Game starting! Get ready!")
                game_running_single = True
                start_time = time.time()
                ball_position = 1
                ball_direction = 1
                ball_speed = 0.2
                right_point = 0
                
            #Left Game Logic
            if game_running_single and is_left:
                elapsed = time.time() - start_time
                # Ball movement
                if ball_position < NUMPIX:
                    update_leds(ball_position)
                    time.sleep(ball_speed)
                    ball_position += ball_direction
                    if ball_position == 0:
                        ball_direction *= -1  # Bounce
                        print("Ball missed! -10 points.")
                        left_point -= 10
                        UART.write(f"Left side miss the ball, total point of left : {left_point}")
                        ball_speed = 0.2  # Reset speed
                    if ball_position == NUMPIX-1:
                        UART.write(f"({ball_position+1}, {ball_speed}, {ball_direction})")
                else:
                    clear_leds()
                    if UART.any():
                        ball_info = UART.read().decode('utf-8').strip()
                        if ball_info[0] == "(":
                            info = eval(ball_info)
                            ball_position = info[0]
                            ball_speed = info[1]
                            ball_direction = info[2]
                        else:
                            print(ball_info)
                    
                # POT interaction during last LEDs
                if ball_position < 2 and ball_direction == -1:
                    twist = PotRead()
                    if twist > 500 or twist < -500:
                        left_point += abs(twist // 100)
                        print(f"Ball hit! +{twist // 100} points.")
                        UART.write(f"Left side hit the ball, total point of left : {left_point}")
                        ball_direction *= -1
                        ball_speed = max(0.05, 0.2 - abs(twist) / 10000)
                    else:
                        print("Missed opportunity to hit!")
            #Right Game Logic
            if game_running_single and is_right:
                elapsed = time.time() - start_time
                # Ball movement
                if ball_position > NUMPIX - 1 and ball_position < NUMPIX*2 :
                    update_leds(2*NUMPIX-1-ball_position)
                    time.sleep(ball_speed)
                    ball_position += ball_direction
                    if ball_position == NUMPIX*2 - 1:
                        ball_direction *= -1  # Bounce
                        print("Ball missed! -10 points.")
                        right_point -= 10
                        UART.write(f"Right side miss the ball, total point of right : {right_point}")
                        ball_speed = 0.2  # Reset speed
                    if ball_position == 10:
                        UART.write(f"({ball_position-1}, {ball_speed}, {ball_direction},)")
                else:
                    clear_leds()
                    if UART.any():
                        ball_info = UART.read().decode('utf-8').strip()
                        if ball_info[0] == "(":
                            info = eval(ball_info)
                            ball_position = info[0]
                            ball_speed = info[1]
                            ball_direction = info[2]
                        else:
                            print(ball_info)
                    
                # POT interaction during last LEDs
                if ball_position > 17 and ball_direction == 1:
                    twist = PotRead()
                    if twist > 500 or twist < -500:
                        print(f"Ball hit! +{twist // 100} points.")
                        right_point += abs(twist// 100)
                        UART.write(f"Right side hit the ball, total point of right : {right_point}")
                        ball_direction *= -1
                        ball_speed = max(0.05, 0.2 - abs(twist) / 10000)
                    else:
                        print("Missed opportunity to hit!")
                    time.sleep(0.1)
            if not game_running_single and UART.any():
                data = UART.readline().decode('utf-8').strip()
                if data == "l":
                    print("Opposite side has choosen left.")
                    print("Right side has choosen.")
                    is_right = True
                elif data == "r":
                    print("Opposite side has choosen right.")
                    print("Left side has choosen.")
                    is_left = True
                if data == "v":
                    print("Left side is ready.")
                    is_left_ready = True
                if data == "b":
                    print("Right side is ready.")
                    is_right_ready = True