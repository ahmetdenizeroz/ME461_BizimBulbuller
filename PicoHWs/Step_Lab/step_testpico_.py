import sys
from machine import Pin
import time

# Initialize LEDs for stepper motor coils
coil_pins = [Pin(2, Pin.OUT), Pin(3, Pin.OUT), Pin(4, Pin.OUT), Pin(5, Pin.OUT)]

# Turn off all coils
def deactivate_coils():
    for pin in coil_pins:
        pin.value(0)

# Activate a sequence
def activate_sequence(sequence):
    for i, value in enumerate(sequence):
        coil_pins[i].value(int(value))

# Continuous run function
def continuous_run(sequences, delay_ms):
    while True:
        for sequence in sequences:
            activate_sequence(sequence)
            time.sleep_ms(delay_ms)
        # Check for stop signal
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            command = sys.stdin.read().strip()
            if command == "STOP":
                deactivate_coils()
                print("STOPPED")
                return

# Main loop
while True:
    print("READY")
    command = input().strip()  # Read from USB serial input
    print(f"RECEIVED: {command}")  # Send feedback to GUI
    if command == "STOP":
        deactivate_coils()
        print("STOPPED")

    elif command.startswith("RUN:"):
        parts = command.split(":")
        delay_ms = int(parts[1])
        sequences = [seq.split() for seq in parts[2].split("|")]
        print("RUNNING")
        continuous_run(sequences, delay_ms)

    else:
        try:
            sequence = [int(x) for x in command.split()]
            activate_sequence(sequence)
            print(f"STEP: {' '.join(command)}")
        except Exception as e:
            print(f"ERROR: {e}")


