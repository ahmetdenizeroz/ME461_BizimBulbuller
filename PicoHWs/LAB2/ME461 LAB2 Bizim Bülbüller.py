#ME461 LAB2 Bizim Bülbüller
from neopixel import Neopixel
import array, time
from machine import Pin, PWM, ADC
import utime


red = (255,0,0)
debounce_time = 10

pot = machine.ADC(26)

delay = 0.5
numpix = 10
strip = Neopixel(numpix, 0, 28, "RGB")

ball_position = numpix - 1
ball_direction = -1
ball_speed = 0.2  # Initial speed in seconds
points = 0
start_time = 0
game_running = False
button = machine.Pin(22, machine.Pin.IN, machine.Pin.PULL_DOWN)

#UART setup

uart = machine.UART(0, baudrate=9600, tx=machine.Pin(0), rx=machine.Pin(1))

class Button():
    def __init__(button, name, pin, state):
        # Initialize a button object with necessary attributes
        button.name = name  # Name of the button (for identification)
        button.last_press_time = time.ticks_ms()  # Tracks the last press time for debounce calculation
        button.button = Pin(pin, Pin.IN, state)  # GPIO Pin and configuration
        button.previous_state = False  # Initialize the previous state to avoid undefined transitions
        button.press_count = 0  # Counter for button presses
        button.isup = False  # Indicates if the button was released after being pressed
        button.isdown = False  # Indicates if the button is currently pressed

    def eliminate_debounce(button, treshold):
        # Method to handle button debounce and state changes
        current_state = button.button.value()  # Read the current state of the button
        if not button.previous_state and current_state:  # Detect button press
            new_time = time.ticks_ms()  # Record current time
            if time.ticks_diff(new_time, button.last_press_time) > treshold:  # Check debounce threshold
                button.previous_state = current_state  # Update the state
                button.last_press_time = new_time  # Update last press time
                button.isup = True  # Set button released flag
                button.isdown = False  # Reset button pressed flag
        elif button.previous_state and not current_state:  # Detect button release
            new_time = time.ticks_ms()  # Record current time
            if time.ticks_diff(new_time, button.last_press_time) > treshold:  # Check debounce threshold
                button.press_count += 1  # Increment press count
                button.previous_state = current_state  # Update the state
                button.last_press_time = new_time  # Update last press time
                button.isup = False  # Reset button released flag
                button.isdown = True  # Set button pressed flag
                

LeftButton = Button("Left", 14, Pin.PULL_DOWN)  # Left button object
RightButton = Button("Right", 22, Pin.PULL_UP)  # Right button object

def ByteDisplay(val):
    global delay
    num = bin(val)[2:] #Number of zeros that will be added
    binary = '0'*(8 - len(num)) + num  # Convert value to binary representation and add the remaining zeros
     # Check the output of whether inputted number is in the range
    print("Current number is:", val)  # Print the number
    print("Binary representation of the number is:", binary)  # Print binary representation
    for i in range(1, 9):
        strip.set_pixel(i, (int(binary[8-i])*255,0,0))  # Turn the corresponsing leds on
    strip.show()
    utime.sleep(delay)
    strip.fill((0,0,0))
    
    LeftButton.eliminate_debounce(debounce_time)  # Handle left button debounce
    RightButton.eliminate_debounce(debounce_time)  # Handle right button debounce
    if LeftButton.isdown:  # Increment the counter if the left button is pressed
        delay += 0.1
        LeftButton.isdown = False  # Reset button state
    if RightButton.isdown:  # Decrement the counter if the right button is pressed
        delay -= 0.1
        RightButton.isdown = False  # Reset button state
   
    print('Delay between numbers is:', delay)    

def PotRead():
    current_value = pot.read_u16()
    time.sleep(0.05)
    next_value = pot.read_u16()
    return next_value - current_value

def clear_leds():
    for i in range(numpix):
        strip.set_pixel(i, (0,0,0))
    strip.show()

def update_leds(position):
    clear_leds()
    strip.set_pixel(position, (0, 255, 0))  
    strip.show()

def game_summary():
    clear_leds()
    for i in range(numpix):
        strip.set_pixel(i , (255,0,0))  # Red flash for game over
        led_strip.write()
        time.sleep(0.1)
    clear_leds()
    


def orchestrate():
    '''
    Function to orchestrate the user input and guide them through the selection
    '''
    return input(
    """
    Welcome, please enter the corresponsing number:
    STEP 1: Binary Counter
    STEP 2: LedPong Single Player
    STEP 3: PotRead data
    STEP 4: LedPong Two Player
    STEP 5: 
    Selection: """)

            
while True:
    #selection = Orchestrate():
        
    selection = orchestrate()
    if selection == '1':
    
        for i in range(0, 255):
            ByteDisplay(i)
    if selection == '2':
        while True:
            if not game_running and button.value():
                print("Game starting! Get ready!")
                game_running = True
                start_time = time.time()
                ball_position = numpix - 1
                ball_direction = -1
                ball_speed = 0.2
                points = 0
    
            if game_running:
                elapsed = time.time() - start_time
            if elapsed >= 60:
                print(f"Game Over! Total Points: {points}")
                game_summary()
                game_running = False
                print("Press the button to restart.")
                continue
        
        # Ball movement
            ball_position += ball_direction
            if ball_position == 0 or ball_position == numpix - 1:
                ball_direction *= -1  # Bounce
                if ball_position == 0:
                    print("Ball missed! -10 points.")
                    points -= 10
                    ball_speed = 0.2  # Reset speed
            update_leds(ball_position)
            time.sleep(ball_speed)
            
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
        while True:
            if not game_running and button.value():
                print("Game starting! Get ready!")
                game_running = True
                start_time = time.time()
                ball_position = numpix - 1
                ball_direction = -1
                ball_speed = 0.2
                points = 0
    
            if game_running:
                elapsed = time.time() - start_time
            if elapsed >= 60:
                print(f"Game Over! Total Points: {points}")
                game_summary()
                game_running = False
                print("Press the button to restart.")
                continue
        
        # Ball movement
            ball_position += ball_direction
            if ball_position == 0 or ball_position == numpix - 1:
                ball_direction *= -1  # Bounce
                if ball_position == 0:
                    print("Ball missed! -10 points.")
                    points -= 10
                    ball_speed = 0.2  # Reset speed
            update_leds(ball_position)
            time.sleep(ball_speed)
            
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
        
            if ball_position == numpix -1:
                uart.write(f"{position}\n")
                time.sleep(0.1)
            
             
            
            

