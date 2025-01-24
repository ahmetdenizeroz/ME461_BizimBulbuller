import tkinter as tk
from tkinter import messagebox
import serial
import time
import threading

# Initialize serial communication with Raspberry Pi Pico
try:
    pico_serial = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
except serial.SerialException as e:
    messagebox.showerror("Connection Error", f"Unable to connect to Pi Pico: {e}")
    pico_serial = None

# Function to send a sequence to the Pico
def send_sequence(sequence):
    if pico_serial:
        pico_serial.write((sequence + '\r\n').encode())
        
        
        
    return None

# Global variables
current_step = 0
stop_continuous_run = False
continuous_thread = None

# Function to apply a single step
def apply_single_step():
    global current_step
    sequence_lines = textbox.get("1.0", tk.END).strip().split("\n")
    if not sequence_lines:
        messagebox.showwarning("Input Error", "No sequences provided.")
        return

    if current_step >= len(sequence_lines):
        current_step = 0  # Loop back to the first sequence

    current_sequence = sequence_lines[current_step].strip()

    try:
        send_sequence(current_sequence)
        current_step_label.config(text=f"Current Step: {current_step + 1}")
        current_step += 1
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send sequence: {e}")

# Function to continuously run the sequence
def run_continuously(sequence_lines):
    global stop_continuous_run, current_step
    stop_continuous_run = False
    current_step = 0

    while not stop_continuous_run:
        if current_step >= len(sequence_lines):
            current_step = 0  # Loop back to the first sequence

        current_sequence = sequence_lines[current_step].strip()
        send_sequence(current_sequence)
        current_step_label.config(text=f"Current Step: {current_step + 1}")
        current_step += 1

        # Dynamically fetch delay from the GUI entry
        try:
            delay = int(delay_entry.get())
            if delay < 0 or delay > 3000:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Input Error", "Delay must be an integer between 0 and 3000 ms.")
            stop_motor()
            return

        time.sleep(delay/1000)  # Convert delay to seconds

# Function to start continuous run
def start_continuous_run():
    global stop_continuous_run, continuous_thread

    sequence_lines = textbox.get("1.0", tk.END).strip().split("\n")
    if not sequence_lines:
        messagebox.showwarning("Input Error", "No sequences provided.")
        return

    if continuous_thread and continuous_thread.is_alive():
        messagebox.showwarning("Already Running", "Continuous run is already in progress.")
        return

    # Start a new thread for the continuous loop
    continuous_thread = threading.Thread(target=run_continuously, args=(sequence_lines,), daemon=True)
    continuous_thread.start()

# Function to stop the motor
def stop_motor():
    global stop_continuous_run
    stop_continuous_run = True
    try:
        send_sequence("STOP")
        current_step_label.config(text="Motor Stopped")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to stop motor: {e}")

# Initialize GUI
root = tk.Tk()
root.title("Stepper Motor Control")

# Textbox for sequences
textbox = tk.Text(root, height=10, width=30)
textbox.insert(tk.END, "1 0 0 0\n0 1 0 0\n0 0 1 0\n0 0 0 1")
textbox.grid(row=0, column=0, padx=10, pady=10, columnspan=3)

# Buttons and Labels
apply_step_button = tk.Button(root, text="Apply Single Step", command=apply_single_step)
apply_step_button.grid(row=1, column=0, padx=5, pady=5)

continuous_run_button = tk.Button(root, text="Continuous Run", command=start_continuous_run)
continuous_run_button.grid(row=1, column=1, padx=5, pady=5)

stop_button = tk.Button(root, text="STOP", command=stop_motor, bg="red", fg="white")
stop_button.grid(row=1, column=2, padx=5, pady=5)

current_step_label = tk.Label(root, text="Current Step: 0")
current_step_label.grid(row=2, column=0, columnspan=3)

delay_label = tk.Label(root, text="Delay (ms):")
delay_label.grid(row=3, column=0)

delay_entry = tk.Entry(root)
delay_entry.insert(0, "50")
delay_entry.grid(row=3, column=1, columnspan=2)

# Start the GUI event loop
root.mainloop()

# Close serial connection when the program exits
if pico_serial:
    pico_serial.close()

