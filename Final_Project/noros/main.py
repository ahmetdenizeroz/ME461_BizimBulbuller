import uasyncio
import network
import time
import machine

# ---- Import your custom modules/classes ----
from romer_minirobot.modules.pico import TwoWheel  # The simple two-wheel class without PID
from romer_minirobot.modules.pico.encoder import Encoder
from romer_minirobot.modules.pico.ultrasonic import Ultrasonic  # If needed
from NeoUser import BeLovedNeo

# ==== Wi-Fi Config ====
SSID = "Redmi"
PASSWORD = "ade654321ade"

# ---- Create Our TwoWheel Object ----
# Adjust pins and freq as needed
two_wheel = TwoWheel(
    name='twoWheel',
    motor1_pins=(6, 7),   # Motor 1: PWM pin1=6, pin2=7
    motor2_pins=(20, 19), # Motor 2: PWM pin1=20, pin2=19
    freq=1000,
    scale=1.0
)

# ---- Initialize Encoders ----
enc1 = Encoder(A=4, B=5, pole_pairs=13, debounce_time=5)    # Encoder for Motor 1
enc2 = Encoder(A=22, B=21, pole_pairs=13, debounce_time=5)  # Encoder for Motor 2

# ---- Onboard LED ----
onboard_led = machine.Pin("LED", machine.Pin.OUT)
onboard_led.value(0)

# ---- Neopixel Setup ----
be_loved_neo = BeLovedNeo(
    n_pixels=10,
    first_half=5,
    second_half=5,
    neo_pin=0,
    blink_intervals=500
)

# ---- Optional: Ultrasonic Sensor ----
# sensor = Ultrasonic(trigger_pin=15, echo_pin=16, timeout=1000)

# Flag to show if a client is connected
client_connected = False

# --------------------------
#  BACKGROUND TASKS
# --------------------------

async def blink_onboard_led(wlan):
    """
    Blink the onboard LED while connecting to Wi-Fi.
    Once connected, keep the LED on solidly.
    """
    while not wlan.isconnected():
        onboard_led.value(1)
        await uasyncio.sleep(0.5)
        onboard_led.value(0)
        await uasyncio.sleep(0.5)
    # Solid ON when connected
    onboard_led.value(1)

async def neopixel_connection_task():
    """
    Manage neopixel connection status.
    Blink if no client is connected; else solid.
    """
    while True:
        be_loved_neo.blink = not client_connected
        be_loved_neo.pc_connection(None)
        await uasyncio.sleep(0.5)

# --------------------------
#  MOTION UTILITY FUNCTIONS
# --------------------------

# Define how many pulses correspond to one 'cell'
STEPS_PER_CELL = 50  # Adjust based on calibration

DUTY_CYCLE = 30000  # 0~65535 => about 45% power. Adjust as needed.

async def move_forward(n_cells: int):
    """
    Move forward by n_cells using encoder counts.
    """
    print(f"[Pico] Moving forward {n_cells} cells.")
    target_pulses = n_cells * STEPS_PER_CELL

    # Reset encoder positions
    enc1.reset_position()
    enc2.reset_position()

    # Set motors forward
    two_wheel.motor1_write(DUTY_CYCLE, True)
    two_wheel.motor2_write(DUTY_CYCLE, True)

    # Monitor encoder positions
    while True:
        pos1 = enc1.get_position()
        pos2 = enc2.get_position()

        if pos1 >= target_pulses and pos2 >= target_pulses:
            break

        await uasyncio.sleep(0.01)  # Check every 10ms

    # Stop motors
    two_wheel.motor1_write(0, True)
    two_wheel.motor2_write(0, True)
    print("[Pico] Forward complete.")

async def move_backward(n_cells: int):
    """
    Move backward by n_cells using encoder counts.
    """
    print(f"[Pico] Moving backward {n_cells} cells.")
    target_pulses = n_cells * STEPS_PER_CELL

    # Reset encoder positions
    enc1.reset_position()
    enc2.reset_position()

    # Set motors backward
    two_wheel.motor1_write(DUTY_CYCLE, False)
    two_wheel.motor2_write(DUTY_CYCLE, False)

    # Monitor encoder positions
    while True:
        pos1 = abs(enc1.get_position())
        pos2 = abs(enc2.get_position())

        if pos1 >= target_pulses and pos2 >= target_pulses:
            break

        await uasyncio.sleep(0.01)  # Check every 10ms

    # Stop motors
    two_wheel.motor1_write(0, True)
    two_wheel.motor2_write(0, True)
    print("[Pico] Backward complete.")

async def turn_degrees(deg: float):
    """
    Rotate the robot by 'deg' degrees using encoder counts.
    Positive 'deg' => Left motor forward, Right motor backward.
    Negative 'deg' => Left motor backward, Right motor forward.
    """
    print(f"[Pico] Turning {deg} degrees.")
    # Define pulses needed per degree (calibrate this value)
    PULSES_PER_DEGREE = 0.3  # Example value, adjust based on calibration
    target_pulses = abs(deg) * PULSES_PER_DEGREE

    # Reset encoder positions
    enc1.reset_position()
    enc2.reset_position()

    if deg > 0:
        # Left motor forward, Right motor backward
        two_wheel.motor1_write(DUTY_CYCLE, False)
        two_wheel.motor2_write(DUTY_CYCLE, True)
    else:
        # Left motor backward, Right motor forward
        two_wheel.motor1_write(DUTY_CYCLE, True)
        two_wheel.motor2_write(DUTY_CYCLE, False)

    # Monitor encoder positions
    while True:
        pos1 = abs(enc1.get_position())
        pos2 = abs(enc2.get_position())

        if pos1 >= target_pulses and pos2 >= target_pulses:
            break

        await uasyncio.sleep(0.01)  # Check every 10ms

    # Stop motors
    two_wheel.motor1_write(0, True)
    two_wheel.motor2_write(0, True)
    print("[Pico] Turn complete.")

async def stop_now():
    """
    Immediately stop all robot motion.
    """
    print("[Pico] Stopping now.")
    two_wheel.motor1_write(0, True)
    two_wheel.motor2_write(0, True)
    await uasyncio.sleep(0.1)  # Brief pause to ensure motors stop

async def dance():
    """
    Perform a fun dance movement: e.g., wiggle back and forth using encoder counts.
    """
    print("[Pico] Dancing!")
    for _ in range(2):
        # Left motor forward, Right motor backward
        two_wheel.motor1_write(DUTY_CYCLE, True)
        two_wheel.motor2_write(DUTY_CYCLE, False)
        await uasyncio.sleep(0.5)
        # Left motor backward, Right motor forward
        two_wheel.motor1_write(DUTY_CYCLE, False)
        two_wheel.motor2_write(DUTY_CYCLE, True)
        await uasyncio.sleep(0.5)
    # Stop motors
    two_wheel.motor1_write(0, True)
    two_wheel.motor2_write(0, True)
    print("[Pico] Dance complete.")

# --------------------------
#  SERVER SETUP & HANDLER
# --------------------------
async def handle_client(reader, writer):
    """
    Handles incoming client connections and commands.
    We only send back 'DONE' or 'ERROR' after the motion/command is finished.
    """
    global client_connected
    client_connected = True
    client_addr = writer.get_extra_info('peername')
    print(f"[Pico] Client connected from {client_addr}!")

    try:
        writer.write(b"Connected to Pico W!\n")
        await writer.drain()

        while True:
            data = await reader.readline()
            if not data:
                print(f"[Pico] Client {client_addr} disconnected.")
                break

            message = data.decode().strip()
            if not message:
                continue  # Skip empty lines

            print(f"[Pico] Received: {message}")
            tokens = message.split(",")
            command = tokens[0].upper()

            try:
                if command == "FORWARD":
                    n = int(tokens[1])
                    await move_forward(n)
                    ack = f"DONE,FORWARD,{n}\n"

                elif command == "BACK":
                    n = int(tokens[1])
                    await move_backward(n)
                    ack = f"DONE,BACK,{n}\n"

                elif command == "TURN":
                    deg = float(tokens[1])
                    await turn_degrees(deg)
                    ack = f"DONE,TURN,{deg}\n"

                elif command == "STOP":
                    await stop_now()
                    ack = "DONE,STOP,0\n"

                elif command == "DANCE":
                    await dance()
                    ack = "DONE,DANCE,0\n"

                else:
                    print(f"[Pico] Unknown command: {message}")
                    ack = "ERROR,UNKNOWN_COMMAND\n"

                # Send acknowledgment after completion
                if writer is not None:
                    writer.write(ack.encode())
                    await writer.drain()
                    print(f"[Pico] Sent: {ack.strip()}")

            except Exception as e:
                print(f"[Pico] Command processing error: {e}")
                error_msg = f"ERROR,{str(e)}\n"
                if writer is not None:
                    writer.write(error_msg.encode())
                    await writer.drain()

    except Exception as e:
        print(f"[Pico] Client connection error: {e}")

    finally:
        print(f"[Pico] Closing connection with {client_addr}...")
        client_connected = False
        if writer is not None:
            await writer.aclose()

async def start_server():
    """
    Connect to Wi-Fi, start the server, keep it running.
    """
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    print("[Pico] Connecting to Wi-Fi...")
    
    # Start background tasks for LED and neopixel
    uasyncio.create_task(blink_onboard_led(wlan))
    uasyncio.create_task(neopixel_connection_task())
    
    # Wait until connected
    while not wlan.isconnected():
        await uasyncio.sleep(1)

    print(f"[Pico] Wi-Fi connected. IP: {wlan.ifconfig()[0]}")

    # Now start the seaarver
    server = await uasyncio.start_server(handle_client, "0.0.0.0", 12346)
    print("[Pico] TCP server started on port 12346.")

    # Keep server alive
    while True:
        await uasyncio.sleep(3600)

# --------------------------
#  MAIN ENTRY
# --------------------------
try:
    #uasyncio.run(start_server())
    #uasyncio.run(move_forward(1))
    uasyncio.run(move_forward(1))
except KeyboardInterrupt:
    # In case we exit via Ctrl+C or similar
    print("[Pico] KeyboardInterrupt detected. Stopping motors and exiting.")
    two_wheel.motor1_write(0, True)
    two_wheel.motor2_write(0, True)
    onboard_led.value(0)
    print("[Pico] Motors stopped and LED turned off.")
