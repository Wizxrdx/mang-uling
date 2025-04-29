#!/usr/bin/env python

import requests
import time
from hx711py.hx711 import HX711
import RPi.GPIO as GPIO
import drivers
import threading
from gpiozero import AngularServo, Device
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep


GPIO.setwarnings(False)
GPIO.cleanup()

# Initialize LCD
display = drivers.Lcd()

# Initialize HX711 modules
hx1 = HX711(23, 24)  # Load Cell 1
hx2 = HX711(27, 22)  # Load Cell 2

reference_unit_1kg_hx1 = 6.709
reference_unit_1kg_hx2 = 4.553

hx1.set_reference_unit(reference_unit_1kg_hx1)
hx2.set_reference_unit(reference_unit_1kg_hx2)

hx1.reset()
hx1.tare()
hx2.reset()
hx2.tare()

display.lcd_display_string("Scale Ready", 1)
time.sleep(1)
display.lcd_clear()

Device.pin_factory = PiGPIOFactory()

# Initialize Servos
servo = AngularServo(6,  min_pulse_width=0.0006, max_pulse_width=0.0023) #bottom left
servo1 = AngularServo(12, min_pulse_width=0.0006, max_pulse_width=0.0023)
servo2 = AngularServo(13, min_pulse_width=0.0006, max_pulse_width=0.0023)
servo3 = AngularServo(18, min_pulse_width=0.0006, max_pulse_width=0.0023)

# Default positions
servo.angle = -40
servo1.angle = 10
servo2.angle = -7
servo3.angle = 0
sleep(1)

# State flags
state = {
    "top_gate_open": False,
    "top_gate_closed": False,
    "bottom_gate_open": False,
    "waiting_for_reset": False,
    "package_ready": False
}

# Shared control flag
should_run = True

# --- Servo control functions ---
def activate_top_servo_open():
    servo2.angle = 90
    servo3.angle = -90
    state["top_gate_open"] = True
    state["top_gate_closed"] = False

def activate_top_servo_close():
    state["top_gate_closed"] = True
    state["package_ready"] = True
    servo2.angle = 0
    servo3.angle = 0
    sleep(2)
    if not state["bottom_gate_open"]:
        threading.Thread(target=activate_bottomservo_for_1kg).start()

'''def activate_bottomservo_for_1kg():
    servo.angle = 10
    servo1.angle = -50
    state["bottom_gate_open"] = True'''

def activate_bottomservo_for_1kg():
    for _ in range(10):
        servo.angle = 10
        servo1.angle = -50
        time.sleep(0.1)  # Keep reapplying angle
    state["bottom_gate_open"] = True

def deactivate_bottomservo():
    servo.angle = -50
    servo1.angle = 10
    state["bottom_gate_open"] = False

def reset_system():
    hx1.tare()
    hx2.tare()
    state["top_gate_open"] = False
    state["top_gate_closed"] = False
    state["waiting_for_reset"] = False
    state["package_ready"] = False
    threading.Thread(target=activate_top_servo_open).start()
    
def finish_1kg():
    requests.put("http://127.0.0.1:5000/count/1kg")

# --- Main control function ---
def run_system():
    global should_run
    try:
        while should_run:
            weight1 = hx1.get_weight(10) / 1000
            weight2 = hx2.get_weight(10) / 1000
            weight1 = max(weight1, 0)
            weight2 = max(weight2, 0)
            total_weight = (weight1 + weight2) / 2
            rounded_weight = round(total_weight, 2)

            display.lcd_display_string("Total Weight:", 1)
            display.lcd_display_string(f"{rounded_weight:>6.2f} kg", 2)
            print(f"[DEBUG] Weight: {rounded_weight:.2f}, States: {state}")

            if not state["top_gate_open"] and rounded_weight <= 0.03:
                threading.Thread(target=activate_top_servo_open).start()

            if state["top_gate_open"] and not state["top_gate_closed"] and 1.00 <= rounded_weight <= 1.20:
                threading.Thread(target=activate_top_servo_close).start()

            if state["bottom_gate_open"] and rounded_weight <= 0.10:
                threading.Thread(target=deactivate_bottomservo).start()
                reset_system()

            time.sleep(0.2)
            finish_10kg()

    except KeyboardInterrupt:
        display.lcd_clear()
        display.lcd_display_string("Program Stopped", 1)
        time.sleep(2)
        display.lcd_clear()