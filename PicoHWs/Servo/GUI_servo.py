import tkinter as tk
from tkinter import messagebox
import serial
import time

# Configure the serial port
SERIAL_PORT = '/dev/ttyACM0'  # Replace with your Pico's COM port
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print("Connected to Raspberry Pi Pico.")
except Exception as e:
    messagebox.showerror("Error", f"Cannot connect to Pico: {e}")
    exit()

def send_command(command):
    """Send a command to the Raspberry Pi Pico."""
    ser.write(f"{command}\r\n".encode())
    

def set_angle(angle):
    """Set the servo angle."""
    send_command(angle)

def release_servo():
    """Release the servo."""
    send_command("stop")
    messagebox.showinfo("Servo Released", "The servo motor is now released.")

def preset_angle():
    """Set the servo to the selected preset angle."""
    angle = preset_var.get()
    set_angle(angle)

def update_slider(val):
    """Send the slider's current value as an angle."""
    set_angle(int(float(val)))

# Create the main GUI window
root = tk.Tk()
root.title("Servo Motor Control")

# Slider for continuous angle adjustment
slider = tk.Scale(root, from_=0, to=180, orient="horizontal", label="Adjust Angle", command=update_slider)
slider.pack(pady=10)

# Radio buttons for preset angles
preset_var = tk.IntVar(value=90)
preset_frame = tk.Frame(root)
tk.Label(preset_frame, text="Preset Angles").pack()
for angle in [0, 45, 90, 135, 180]:
    tk.Radiobutton(preset_frame, text=f"{angle}°", variable=preset_var, value=angle, command=preset_angle).pack(anchor="w")
preset_frame.pack(pady=10)

# Release button
release_button = tk.Button(root, text="Release Servo", command=release_servo, bg="red", fg="white")
release_button.pack(pady=10)

# Run the GUI loop
root.mainloop()

# Close the serial connection when the GUI is closed
ser.close()
