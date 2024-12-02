#ME461 LAB2 Bizim Bülbüller
from neopixel import Neopixel
import array, time
from machine import Pin, PWM, ADC
import utime

red = (255,0,0)
debounce_time = 10

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
                
delay = 0.5
numpix = 10
strip = Neopixel(numpix, 0, 28, "RGB")

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
   
    print(delay)    

def Orchestrate():
    '''
    Function to orchestrate the user input and guide them through the selection
    '''
    return input(
    """
    Welcome, please enter the corresponsing number:
    STEP 1: 
    STEP 2: 
    STEP 3: 
    STEP 4: 
    STEP 5: 
    Selection: """)

            
while True:
    #selection = Orchestrate():
        

    for i in range(0, 255):
        ByteDisplay(i)
    #if selection == '2':
        
             
            
            

