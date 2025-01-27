import serial
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import time
import threading

# Serial Configuration
SERIAL_PORT = "/dev/ttyACM0"  # Change this if needed
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)  # Faster response time
    time.sleep(2)  # Wait for connection
    print("Connected to Raspberry Pi Pico.")
except Exception as e:
    messagebox.showerror("Error", f"Cannot connect to Pico: {e}")
    exit()

# ========== GUI SETUP ==========
root = tk.Tk()
root.title("DC Motor Control")
root.geometry("400x600")  # Adjusted for better layout

# Status Label
status_label = tk.Label(root, text="Waiting for command...", font=("Arial", 10))
status_label.pack(pady=5)

# Command Log (Scrollable Text Box)
command_log_label = tk.Label(root, text="Command Log:")
command_log_label.pack()

command_log = scrolledtext.ScrolledText(root, height=8, width=50, state="normal")
command_log.pack(pady=5)

# ========== SERIAL COMMAND FUNCTION ==========
def send_command(command):
    """Send a command to the Raspberry Pi Pico in a separate thread to prevent UI blocking."""
    def task():
        try:
            ser.write(f"{command}\r\n".encode())  # Send command
            time.sleep(0.1)  # Small delay for stability
            response = ser.readline().decode().strip()  # Read response
            
            # Update the GUI safely in the main thread
            root.after(0, lambda: status_label.config(text=f"Pico: {response}"))

            # Log sent command in the text box
            root.after(0, lambda: command_log.insert(tk.END, f"Sent: {command}, Received: {response}\n"))
            root.after(0, lambda: command_log.see(tk.END))  # Auto-scroll to latest entry

            print(f"Sent: {command}, Received: {response}")  # Debugging log
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Error", f"Failed to send command: {e}"))

    # Run the task in a separate thread to prevent UI blocking
    threading.Thread(target=task, daemon=True).start()

# ========== PWM & DUTY CYCLE ==========
def set_pwm(value):
    """Convert slider value to integer and send PWM command."""
    pwm_value = int(float(value))
    send_command(str(pwm_value))

def set_duty_cycle(percentage):
    """Convert duty cycle percentage to PWM range and send command."""
    pwm_value = int((percentage / 100) * 65535)
    send_command(str(pwm_value))

# ========== MOTOR CONTROLS ==========
def motor_direction(clockwise):
    send_command("clockwise" if clockwise else "counterclockwise")

def stop_motor():
    send_command("stop")

# ========== GUI COMPONENTS ==========

# PWM Slider
pwm_label = tk.Label(root, text="Adjust Motor Speed (PWM)")
pwm_label.pack()

pwm_slider = ttk.Scale(root, from_=0, to=65535, orient="horizontal", command=set_pwm)
pwm_slider.set(32767)  # Default value at 50% duty cycle
pwm_slider.pack(pady=5)

# Duty Cycle Slider
duty_cycle_label = tk.Label(root, text="Adjust Duty Cycle (%)")
duty_cycle_label.pack()

duty_cycle_slider = ttk.Scale(root, from_=0, to=100, orient="horizontal", command=lambda v: set_duty_cycle(float(v)))
duty_cycle_slider.set(50)  # Default at 50%
duty_cycle_slider.pack(pady=5)

# Duty Cycle Preset Buttons
frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=5)

for percent in [0, 25, 50, 75, 100]:
    btn = tk.Button(frame_buttons, text=f"{percent}%", command=lambda p=percent: set_duty_cycle(p))
    btn.pack(side="left", padx=5)

# Motor Direction Buttons
tk.Button(root, text="Clockwise", command=lambda: motor_direction(True)).pack(pady=5)
tk.Button(root, text="Counterclockwise", command=lambda: motor_direction(False)).pack(pady=5)

# Stop Button
tk.Button(root, text="STOP", command=stop_motor, fg="white", bg="red", font=("Arial", 12, "bold")).pack(pady=10)

# ========== SAFE EXIT HANDLING ==========
def on_closing():
    ser.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()

