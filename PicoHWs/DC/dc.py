import machine
import time
import sys

# Pin configuration for Motor 1
motor1_in1 = machine.Pin(2, machine.Pin.OUT)
motor1_in2 = machine.Pin(3, machine.Pin.OUT)
pwm1_pin = machine.PWM(machine.Pin(4))

# Pin configuration for Motor 2
motor2_in1 = machine.Pin(8, machine.Pin.OUT)
motor2_in2 = machine.Pin(9, machine.Pin.OUT)
pwm2_pin = machine.PWM(machine.Pin(10))

# PWM frequency
pwm1_pin.freq(5000)
pwm2_pin.freq(5000)

# Default PWM value (50% duty cycle)
pwm_value = 32767  
current_direction = None  # Track current movement direction

def stop_motors():
    """Stop both motors immediately by setting all control pins to LOW and stopping PWM."""
    motor1_in1.value(0)
    motor1_in2.value(0)
    motor2_in1.value(0)
    motor2_in2.value(0)
    pwm1_pin.duty_u16(0)  # Stop PWM signal
    pwm2_pin.duty_u16(0)
    print("Motors stopped.")

# Set initial state
stop_motors()

while True:
    try:
        user_input = sys.stdin.readline().strip().lower()  # Read input from GUI

        if not user_input:
            continue  # Ignore empty input

        print(f"Received command: {user_input}")  # Debugging output

        if user_input == "stop":
            stop_motors()
            current_direction = None  # Reset direction
            continue

        elif user_input == "clockwise":
            motor1_in1.value(1)
            motor1_in2.value(0)
            motor2_in1.value(1)
            motor2_in2.value(0)
            current_direction = "clockwise"
            print(f"Rotating clockwise at PWM {pwm_value}")
            pwm1_pin.duty_u16(pwm_value)
            pwm2_pin.duty_u16(pwm_value)

        elif user_input == "counterclockwise":
            motor1_in1.value(0)
            motor1_in2.value(1)
            motor2_in1.value(0)
            motor2_in2.value(1)
            current_direction = "counterclockwise"
            print(f"Rotating counterclockwise at PWM {pwm_value}")
            pwm1_pin.duty_u16(pwm_value)
            pwm2_pin.duty_u16(pwm_value)

        else:
            try:
                new_pwm_value = int(user_input)
                if 0 <= new_pwm_value <= 65535:
                    pwm_value = new_pwm_value  # Store the new PWM value
                    if current_direction:  # Only update if motors are running
                        pwm1_pin.duty_u16(pwm_value)
                        pwm2_pin.duty_u16(pwm_value)
                    print(f"PWM updated to {pwm_value}")
                else:
                    print("Invalid PWM value. Must be between 0 and 65535.")
            except ValueError:
                print("Invalid input. Enter an integer (PWM value) or 'clockwise'/'counterclockwise'.")

    except KeyboardInterrupt:
        print("\nExiting motor control mode.")

