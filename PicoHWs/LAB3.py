from machine import Pin, ADC
import utime

# Define QRD1114 sensor inputs (analog)
qrd_A = ADC(26)  # First QRD sensor
qrd_B = ADC(27)  # Second QRD sensor

# Define button inputs with pull-ups
button_L = Pin(16, Pin.IN, Pin.PULL_DOWN)
button_R = Pin(17, Pin.IN, Pin.PULL_DOWN)

# Encoder Variables
encoder_count = 0
last_state_A = 0
last_state_B = 0
encoding_modes = [1, 2, 4]  # Encoding mode cycle X1 → X2 → X4
current_mode_index = 0  # Start with X1 mode

# Debounce variables
last_press_L = 0
last_press_R = 0
DEBOUNCE_TIME = 200  # milliseconds

# Interrupt Handlers
def button_L_handler(pin):
    global current_mode_index, last_press_L
    current_time = utime.ticks_ms()
    
    if utime.ticks_diff(current_time, last_press_L) > DEBOUNCE_TIME:
        current_mode_index = (current_mode_index + 1) % len(encoding_modes)  # Cycle through modes
        print("Encoding mode:", "X1" if encoding_modes[current_mode_index] == 1 else "X2" if encoding_modes[current_mode_index] == 2 else "X4")
        last_press_L = current_time

def button_R_handler(pin):
    global encoder_count, last_press_R
    current_time = utime.ticks_ms()
    
    if utime.ticks_diff(current_time, last_press_R) > DEBOUNCE_TIME:
        encoder_count = 0
        print("Encoder reset")
        last_press_R = current_time

# Attach interrupts to buttons
button_L.irq(trigger=Pin.IRQ_FALLING, handler=button_L_handler)
button_R.irq(trigger=Pin.IRQ_FALLING, handler=button_R_handler)

def read_qrd(sensor):
    """Read the QRD1114 sensor and return a binary value based on a threshold."""
    value = sensor.read_u16()  # Read analog value (0-65535)
    return 1 if value < 10000 else 0  # Adjust threshold as needed

while True:
    # Read current state of QRD sensors
    state_A = read_qrd(qrd_A)
    state_B = read_qrd(qrd_B)
    print("A", qrd_A.read_u16())
    print("B", qrd_B.read_u16())
    #alttakiB
    

    encoding_mode = encoding_modes[current_mode_index]  # Get current encoding mode

    if encoding_mode == 1:  # X1 encoding
        if state_A == 1 and last_state_A == 0:  # Detect rising edge of A
            encoder_count += 1 if state_B == 0 else -1

    elif encoding_mode == 2:  # X2 encoding
        if state_A == 1 and last_state_A == 0:  # Detect any change in A
            encoder_count += 1 if state_B == 0 else -1
        elif state_A == 0 and last_state_A == 1:
            encoder_count += 1 if state_B == 1 else -1

    elif encoding_mode == 4:  # X4 encoding
        if state_A == 1 and last_state_A == 0:  # Detect any change in A
            encoder_count += 1 if state_B == 0 else -1
        elif state_A == 0 and last_state_A == 1:
            encoder_count += 1 if state_B == 1 else -1
        elif state_B == 1 and last_state_B == 0:
            encoder_count += 1 if state_A == 1 else -1
        elif state_B == 0 and last_state_B == 1:
            encoder_count += 1 if state_A == 0 else -1

    # Store last states for edge detection
    last_state_A = state_A
    last_state_B = state_B

    print("Encoder Count:", encoder_count)
    utime.sleep_ms(200)  # Small delay to stabilize readings
