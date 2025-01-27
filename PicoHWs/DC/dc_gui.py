import serial
import tkinter as tk
from tkinter import messagebox, ttk
import time

# Serial Configuration
SERIAL_PORT = "/dev/ttyACM0"  # Change if needed
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)  # Faster response time
    time.sleep(2)  # Wait for connection
    print("Connected to Raspberry Pi Pico.")
except Exception as e:
    messagebox.showerror("Error", f"Cannot connect to Pico: {e}")
    exit()

def send_command(command):
    """Send a command to the Raspberry Pi Pico and execute it immediately."""
    try:
        ser.write(f"{command}\r\n".encode())  # Send command
        time.sleep(0.002)# Ensure immediate execution
        response = ser.readline().decode().strip()  # Read response
        status_label.config(text=f"Pico: {response}")  # Update GUI status
        print(f"Sent: {command}, Received: {response}")  # Debugging log
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send command: {e}")

def set_pwm(value):
    """Continuously send PWM value as integer while the slider is moving."""
    try:
        pwm_value = round(float(value))
        if 0 <= pwm_value <= 65535:
            send_command(pwm_value)  # Send raw PWM value
        else:
            messagebox.showerror("Error", "PWM value must be between 0 and 65535.")
    except ValueError:
        messagebox.showerror("Error", "Invalid PWM value.")

def motor_direction(clockwise):
    """Immediately send motor direction command."""
    send_command("clockwise" if clockwise else "counterclockwise")

# GUI Setup
root = tk.Tk()
root.title("DC Motor Control")

# Label for the PWM Slider
pwm_label = tk.Label(root, text="Adjust Motor Speed (PWM)")
pwm_label.pack()

# Continuous PWM Slider (Now updates continuously)
pwm_slider = ttk.Scale(root, from_=0, to=65535, orient="horizontal", command=set_pwm)
pwm_slider.set(0)  # Default value
pwm_slider.pack(pady=10)

# Motor Direction Buttons (Instant Execution)
clockwise_button = tk.Button(root, text="Clockwise", command=lambda: motor_direction(True))
clockwise_button.pack(pady=5)

counterclockwise_button = tk.Button(root, text="Counterclockwise", command=lambda: motor_direction(False))
counterclockwise_button.pack(pady=5)

# Status Label to Display Responses from Pico
status_label = tk.Label(root, text="Waiting for command...")
status_label.pack(pady=10)

# Run GUI
root.mainloop()

# Close serial connection when GUI is closed
ser.close()

