import machine
import time

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

delay_ms = 10  # Delay between movements

while True:
    try:
        user_input = input().strip().lower()  # Read input from the GUI
        if user_input == "stop":
            print("Stopping motors.")
            break

        elif user_input == "clockwise":
            motor1_in1.value(1)
            motor1_in2.value(0)
            motor2_in1.value(1)
            motor2_in2.value(0)
            print("Now rotating clockwise.")

        elif user_input == "counterclockwise":
            motor1_in1.value(0)
            motor1_in2.value(1)
            motor2_in1.value(0)
            motor2_in2.value(1)
            print("Now rotating counterclockwise.")

        else:
            try:
                pwm_value = int(user_input)
                if 0 <= pwm_value <= 65535:
                    pwm1_pin.duty_u16(pwm_value)
                    pwm2_pin.duty_u16(pwm_value)
                    print(f"PWM set to {pwm_value}")
                else:
                    print("Invalid PWM value. Must be between 0 and 65535.")
            except ValueError:
                print("Invalid input. Enter an integer (PWM value) or 'clockwise'/'counterclockwise'.")
        
        time.sleep_ms(delay_ms)

    except KeyboardInterrupt:
        print("\nExiting motor control mode.")
        break

