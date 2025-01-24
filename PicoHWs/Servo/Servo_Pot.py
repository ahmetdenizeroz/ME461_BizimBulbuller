from machine import Pin, PWM, ADC
from time import sleep

# Initialize potentiometer on ADC0 (Pin 26)
potentiometer = ADC(Pin(26))

# Initialize servo on GPIO Pin 0 with PWM
servo = PWM(Pin(0))
servo.freq(50)  # 50Hz frequency for servo control

def set_servo_angle(angle):
    """
    Converts an angle (0-180) to a duty cycle and sets the servo position.
    """
    pulse_width = int(500 + (angle / 180) * 2000)  # Map 0-180° to 500-2500µs
    duty_u16 = int(pulse_width * 65535 // 20000)  # Convert to 16-bit duty
    servo.duty_u16(duty_u16)

try:
    while True:
        # Read potentiometer value (0-65535)
        pot_value = potentiometer.read_u16()
        
        # Map potentiometer value (0-65535) to angle (0-180)
        angle = int(180-(pot_value / 65535) * 180)
        
        # Set servo to the mapped angle
        set_servo_angle(angle)
        
        # Debugging: Print potentiometer and angle values
        print(f"Potentiometer Value: {pot_value}, Servo Angle: {angle}")
        
        sleep(0.1)  # Small delay for smoother updates
except KeyboardInterrupt:
    # Release the servo on exit
    servo.deinit()
    print("\nServo released. Program exited.")


