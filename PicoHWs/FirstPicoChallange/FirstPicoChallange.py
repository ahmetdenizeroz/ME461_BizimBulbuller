import machine
import time
import math

led = machine.Pin("LED", machine.Pin.OUT)
temp_sensor = machine.ADC(4)

def Startup():
    
    print('''
    1. LED Blink
    2. Hearth Beat
    3. Calculator
    4. Display Onboard Temperature Reading
    5. Reverse the Given Text
    ''')
    return input("Enter Your Selection: ")

def LedBlink():
    NumberOfBlinks = int(input("Please enter number of blinks required as Integer: "))
    DurationOfBlinks = input("Please enter duration of one blink in ms or inf: ")
    try:
        if DurationOfBlinks == "inf":
            while True:
                led.on()
    
        else:
            DurationOfBlinks = int(DurationOfBlinks) / 1000
        
            for blink in range(0, NumberOfBlinks):
                led.on()
                time.sleep(DurationOfBlinks/2)
                led.off()
                time.sleep(DurationOfBlinks/2)
                
    except KeyboardInterrupt:
        led.off()
        Startup()

def HearthBeat():
    def beaton(increment):
        duration = increment / 1000
        led.on()
        time.sleep(duration)
        led.off()
        time.sleep(0.02 - duration)
    def beatoff(increment):
        duration = increment / 1000
        led.on()
        time.sleep(0.02 - duration)
        led.off()
        time.sleep(duration)
        
    NumberOfBeats = int(input("Please enter number of beats required as Integer: "))
    DurationOfBeats = input("Please enter duration of one beat in ms or inf: ")
    
    try:
        if DurationOfBeats == "inf":
            for i in range(0, 50):
                increment = 20 / 50
                beaton(i * increment)
            while True:
                led.on()
        else:
            DurationOfBeats = int(DurationOfBeats) / 2
            iteration = int(DurationOfBeats / 20)
            for beat in range(0, NumberOfBeats):
                for i in range(0, iteration):
                    increment = 20 / iteration
                    beaton(i * increment)
                for i in range(0, iteration):
                    increment = 20 / iteration
                    beatoff(i * increment)
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        led.off()
        Startup()
    return
    
def Calculator():
    while True:
        try:
            calculation = input("Please enter the prompt: ")
            print(eval(calculation))
        except KeyboardInterrupt:
            Startup()
        except:
            print("Prompt is Failed to Evaluate. Please try again: ")

def Temperature():
    try:
        while True:
            for t in range(0, 3):
                raw = temp_sensor.read_u16()
                volt = (3.3/65535) * raw
                temperature = 27 - (volt - 0.706) / 0.001721
                print("{:.2f}".format(temperature) + "°")
                time.sleep(0.3333333333)
    except KeyboardInterrupt:
        Startup()
        
def TextReverser():
    try:
        while True:
            text = input("Please enter the text to be reversed: ")
            print("".join(reversed(text)))
    except KeyboardInterrupt:
        Startup()

while True:
    selection = Startup()
    if selection == "1":
        LedBlink()
    elif selection == "2":
        HearthBeat()
    elif selection == "3":
        Calculator()
    elif selection == "4":
        Temperature()
    elif selection == "5":
        TextReverser()
        
    
    