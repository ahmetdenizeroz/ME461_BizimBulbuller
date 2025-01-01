import time
from machine import Pin, ADC
import neopixel

# Variables for general configuration
debounce_time = 10  # Time (in ms) to avoid button bouncing errors
frequency = 5000  # Frequency of PWM signal in Hz

# Class to handle button operations with debouncing
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

# Defining LED pins
#led_pins = [2, 3, 4, 5, 6, 7, 8, 9]  # GPIO pins for LEDs

# Defining Neopixel
np = neopixel.NeoPixel(machine.Pin(2), 8)


# Defining the right and left buttons
LeftButton = Button("Left", 14, Pin.PULL_DOWN)  # Left button object
RightButton = Button("Right", 22, Pin.PULL_UP)  # Right button object

# Defining Potentiometer
Potentiometer = ADC(26)  # ADC pin for reading potentiometer values

# Initializing LEDs as PWM outputs
#leds = {}  # Dictionary to store LED objects
#for x in range(8):
#    leds[x + 1] = PWM(Pin(led_pins[x], Pin.OUT))  # Create PWM object for each LED
#    leds[x + 1].freq(frequency)  # Set PWM frequency for each LED
#print(leds)  # Print the dictionary of LEDs

# Byte Display Function
def ByteDisplay(val=0):
    '''
    Displays the given number in binary format on the LEDs.

    Parameters:
        val (int): An integer between 0 and 255 to be displayed.
    '''
    binary = decimal_to_Binary(val)  # Convert value to binary representation
    if binary is not None:  # Check the output of whether inputted number is in the range
        print("Current number is:", val)  # Print the number
        print("Binary representation of the number is:", binary)  # Print binary representation
        for i in range(1, 9):
            np[int(binary[8 - i]) * i] = (255, 0, 0)  # Turn the corresponsing leds on
    else:
        return

# Volta Function
def Volta(N=1, speed=0.1):
    '''
    Turns LEDs on one at a time from right to left, then back, for a given number of cycles.

    Parameters:
        N (int): Number of cycles.
        speed (float): Duration (in seconds) for which each LED stays on.
    '''
    for Step in range(N):  # Perform N cycles
        for led in range(1, 9):  # Turn LEDs on from right to left
            np[led] = (0, 255, 0)  # Turn on the current LED
            time.sleep(speed)  # Wait for the specified duration
            np[led] = (0, 255, 0)  # Turn off the current LED
        for led in range(2, 9):  # Turn LEDs on from left to right
            np[9 - led] = (0, 255, 0)  # Turn on the current LED
            time.sleep(speed)  # Wait for the specified duration
            np[9 - led] = (0, 255, 0)  # Turn off the current LED
        time.sleep(speed)  # Pause between cycles

# Snake Function
        '''
def Snake(L=3, speed=0.1):
    '''
#    Creates a snake-like LED pattern where multiple LEDs light up and move across the strip.
#
#    Parameters:
#        L (int): Length of the snake (number of LEDs lit at a time).
#        speed (float): Speed of the snake movement (in seconds).
    '''
    step = int(65536 / L)  # Calculate step brightness for fading effect
    while True:
        for led in range(1, 9):  # Move the snake from right to left
            for body in range(L + 1):  # Light up LEDs based on snake length
                try:
                    leds[led - body].duty_u16(65536 - body * step)  # Set LED brightness
                except:
                    continue  # Ignore errors for out-of-range LEDs
            time.sleep(speed)  # Wait for the specified duration
        for led in range(2, 9):  # Move the snake from left to right
            for body in range(L + 1):
                try:
                    leds[9 - (led - body)].duty_u16(65536 - body * step)  # Set LED brightness
                except:
                    continue  # Ignore errors for out-of-range LEDs
            time.sleep(speed)  # Wait for the specified duration
        '''
# Button Counter Function
def ButtonCounter():
    '''
    Increments or decrements a counter based on button presses and displays the value on LEDs.
    '''
    number = int(time.ticks_ms()) % 255  # Initialize counter, randomized by using time 
    ByteDisplay(number)  # Display the initial value
    while True:
        LeftButton.eliminate_debounce(debounce_time)  # Handle left button debounce
        RightButton.eliminate_debounce(debounce_time)  # Handle right button debounce
        if LeftButton.isdown:  # Increment the counter if the left button is pressed
            number += 1
            ByteDisplay(number)  # Update display
            LeftButton.isdown = False  # Reset button state
        if RightButton.isdown:  # Decrement the counter if the right button is pressed
            number -= 1
            ByteDisplay(number)  # Update display
            RightButton.isdown = False  # Reset button state
        time.sleep(0.1)  # Small delay to avoid rapid polling
        '''
# Digital VU Meter Function
def DigitalVUMeter():
    '''
#    Simulates a VU meter using LEDs to display the analog input value.
    '''
    while True:
        last_led = 0  # Tracks the last LED lit
        adc_value = Potentiometer.read_u16()  # Read analog value from potentiometer
        numofleds = int(adc_value / (65536 / len(led_pins)))  # Calculate number of LEDs to light up
        increment = adc_value % int(65536 / len(led_pins))  # Calculate brightness of the next LED
        for led in range(1, numofleds + 1):
            leds[led].duty_u16(65536)  # Turn on full brightness for the LEDs
            last_led = led  # Update the last lit LED
        leds[last_led + 1].duty_u16(increment)  # Partially light the next LED
        for others in range(last_led + 2, len(led_pins) + 1):
            leds[others].duty_u16(0)  # Turn off remaining LEDs
        time.sleep(0.1)  # Small delay to update smoothly
    '''
# Helper function to convert a number to 8-bit binary
def decimal_to_Binary(n):
    '''
    Converts an integer to an 8-bit binary string.

    Parameters:
        n (int): The integer to convert (0 to 255).

    Returns:
        str: 8-bit binary string representation.
    '''
    # Check if the input number is within the valid range (0 to 255).
    if n >= 0 and n<256:
        # Convert the number to binary using the bin() function.
        # bin(n) returns a string with a prefix '0b' (e.g., bin(5) returns '0b101').
        # By using [2:], we remove the '0b' prefix to get just the binary digits.
        temp = bin(n)[2:]
        # Add leading zeros to make sure the binary string is always 8 bits long.
        # The '8 - len(temp)' calculates how many leading zeros are needed.
        # '0'*(8 - len(temp)) creates a string of that many zeros and appends it to 'temp'.
        binary = '0'*(8 - len(temp)) + temp
        return binary # Return the 8-bit binary string.
    else: 
        # If the number is outside the valid range (0 to 255), print an error message.
        print("Entered value is out of the range!")
        return

def ledreset():
    '''
    Iterating through each LED and setting the duty cycle to 0 (turns them off)
    '''
    for led in range(0, 9):
            np[led] = (0, 0, 0)


def Orchestrate():
    '''
    Function to orchestrate the user input and guide them through the selection
    '''
    return input(
    """
    Welcome, please enter the corresponsing number:
    STEP 1: Byte Display
    STEP 2: Walking Lights
    STEP 3: Walking & Fading lights
    STEP 4: Button Counter
    STEP 5: Digital VU Meter
    Selection: """)

# Main loop that controls the flow of the program
while True:
    ledreset()  # Reset all LEDs to off before each iteration
    choose = Orchestrate()  # Prompt the user to select an option

    # If the user selects '1', enter Byte Display mode
    if choose == "1":
        try:
            while True:
                # Ask user for a number between 0 and 255
                val = int(input("Please enter an integer between 0 and 255: "))
                ByteDisplay(val)  # Display the binary representation of the number on LEDs
        except KeyboardInterrupt:  # Exit when interrupted (Ctrl+C)
            Orchestrate()  # Return to the menu
    
    # If the user selects '2', enter Walking Lights mode
    if choose == "2":
        try:
            # Get the number of cycles for the walking lights effect
            N = int(input("Please enter number of voltas: "))
            # Get the speed (time in seconds) between LED transitions
            Speed = float(input("Please enter the speed as seconds: "))
            Volta(N, Speed)  # Execute the walking lights effect
        except KeyboardInterrupt:
            Orchestrate()  # Return to the menu
            Snake(L = 3, speed = 0.1)  # If interrupted, start the snake effect with default parameters
    
    # If the user selects '3', enter Walking & Fading lights mode (Snake)
    if choose == "3":
        try:
            # Get the length of the snake
            L = int(input("Please enter length of the snake: "))
            # Get the speed for the snake's movement
            Speed = float(input("Please enter the speed in seconds: "))
            Snake(L, Speed)  # Execute the snake effect
        except KeyboardInterrupt:
            Orchestrate()  # Return to the menu
    
    # If the user selects '4', enter Button Counter mode
    if choose == "4":
        try:
            ButtonCounter()  # Start counting button presses
        except KeyboardInterrupt:
            Orchestrate()  # Return to the menu

    # If the user selects '5', enter Digital VU Meter mode
    if choose == "5":
        try:
            DigitalVUMeter()  # Start the digital VU meter based on potentiometer input
        except KeyboardInterrupt:
            Orchestrate()  # Return to the menu
