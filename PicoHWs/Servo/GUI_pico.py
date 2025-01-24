from machine import Pin
from time import sleep, sleep_us

# Initialize servo control pin
from machine import Pin
from time import sleep, sleep_us

# Initialize servo control pin
servo_pin = Pin(0,Pin.OUT)

def send_signal(pulse_width):
    """
    Generates a single pulse for the servo based on the pulse width (in microseconds).
    """
    servo_pin.value(1)  # Set pin high
    sleep_us(pulse_width)
    servo_pin.value(0)  # Set pin low
    sleep_us(20000 - pulse_width)  # Complete the 10ms period

def manual_control():
    """
    Reads input from the user and generates appropriate servo signals.
    """
    try:
        while True:
            user_input = input("Enter angle (0-180) or 'stop': ").strip().lower()
            
            if user_input == "stop":
                print("Stopping PWM signal. Servo released.")
                break
            
            try:
                angle = int(user_input)
                if 0 <= angle <= 180:
                    pulse_width = int(500 + (angle / 180.0) * 2000)  # Map angle to 0.5ms-2.5ms
                    print(f"Moving to angle: {angle}°")
                    for _ in range(1):  # Send signal for ~1 second
                        send_signal(pulse_width)
                else:
                     print("Invalid angle. Enter a value between 0 and 180.")
            except ValueError:
                print("Invalid input. Enter an integer angle or 'stop'.")
    except KeyboardInterrupt:
        print("\nExiting manual control mode.")

manual_control()

