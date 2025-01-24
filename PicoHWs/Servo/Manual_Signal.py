import time
from servo import Servo

# Create our Servo object, assigning the
# GPIO pin connected to the PWM wire of the servo
my_servo = Servo(pin_id=0)

delay_ms = 10  # Amount of milliseconds to wait between servo movements

while True:
    try:
        user_input = input("Enter angle (0-180) or 'stop': ").strip().lower()
        if user_input == "stop":
            print("Stopping PWM signal. Servo released.")
            break

        try:
            angle = int(user_input)
            if 0 <= angle <= 180:
                my_servo.write(angle)  # Set the Servo to the current position
                time.sleep_ms(delay_ms)  # Wait for the servo to make the movement
            else:
                print("Invalid angle. Enter a value between 0 and 180.")
        except ValueError:
            print("Invalid input. Enter an integer angle or 'stop'.")
    except KeyboardInterrupt:
        print("\nExiting manual control mode.")
        break


