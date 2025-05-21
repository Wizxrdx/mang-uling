#!/usr/bin/env python

import time
import requests
import serial
from hx711py.hx711 import HX711
import RPi.GPIO as GPIO
import drivers
import threading
from gpiozero import AngularServo, Device
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep

name = "5kg"

GPIO.setwarnings(False)
GPIO.cleanup()

# Initialize LCD
display = drivers.Lcd()

CONTROL_PIN = 21
GPIO.setmode(GPIO.BCM)
GPIO.setup(CONTROL_PIN, GPIO.OUT)

# Activate Arduino logic
GPIO.output(CONTROL_PIN, GPIO.HIGH)

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

VIBRATOR1_PIN = 4
VIBRATOR2_PIN = 26
GPIO.setup(VIBRATOR1_PIN, GPIO.OUT)
GPIO.setup(VIBRATOR2_PIN, GPIO.OUT)

# Initialize vibrator motors as OFF
GPIO.output(VIBRATOR1_PIN, GPIO.LOW)
GPIO.output(VIBRATOR2_PIN, GPIO.LOW)

try:
    arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=2)
    time.sleep(3)
    print("[INFO] Arduino connected on /dev/ttyACM0")
except serial.SerialException as e:
    arduino = None
    print(f"[ERROR] Arduino connection failed: {e}")


# Initialize HX711 modules
hx1 = HX711(23, 24)  # Load Cell 1
hx2 = HX711(27, 22)  # Load Cell 2

reference_unit_5kg_hx1 = 8.966
reference_unit_5kg_hx2 = 4.413


hx1.set_reference_unit(reference_unit_5kg_hx1)
hx2.set_reference_unit(reference_unit_5kg_hx2)

hx1.reset()
hx1.tare()
hx2.reset()
hx2.tare()

def center_text(text, width=16):
    return text.center(width)

display.lcd_display_string(center_text("    System Ready"), 1)
display.lcd_display_string(center_text("    Press  START"), 2)

Device.pin_factory = PiGPIOFactory()
servo_lock = threading.Lock()

# Initialize Servos
servo = AngularServo(6,  min_pulse_width=0.0006, max_pulse_width=0.0023) #bottom left
servo1 = AngularServo(12, min_pulse_width=0.0006, max_pulse_width=0.0023) #bottom right
servo2 = AngularServo(18, min_pulse_width=0.0006, max_pulse_width=0.0023) # top left
servo3 = AngularServo(13, min_pulse_width=0.0006, max_pulse_width=0.0023) # top right

# Default positions
servo.angle = -30
servo1.angle = -20
servo2.angle = -36
servo3.angle = 26
sleep(1)

# State flags
state = {
    "top_gate_open": False,
    "top_gate_closed": False,
    "bottom_gate_open": False,
    "waiting_for_reset": False,
    "package_ready": False,
    "sack_detected": False
}

# Shared control flag
should_run = True

# --- Servo control functions ---
def activate_top_servo_open():
    with servo_lock:
        if not state["top_gate_open"]:
            servo2.angle = -80
            servo3.angle = 75
            state["top_gate_open"] = True
            state["top_gate_closed"] = False

            # Turn ON vibrator when top gate opens

            GPIO.output(VIBRATOR1_PIN, GPIO.LOW)  # Optional, if you're using 2
            GPIO.output(VIBRATOR2_PIN, GPIO.HIGH)
            print("[INFO] Top gate opened, vibrator ON")

def activate_top_servo_close():
    with servo_lock:
        if state["top_gate_open"] and not state["top_gate_closed"]:
            # Turn OFF vibrator when top gate closes
            GPIO.output(VIBRATOR1_PIN, GPIO.LOW)
            GPIO.output(VIBRATOR2_PIN, GPIO.LOW)
            time.sleep(0.5)  #Wait 5 seconds
            print("[INFO] Top gate closed, vibrator OFF")
            servo2.angle = -36
            servo3.angle = 26
            time.sleep(2)
            state["top_gate_closed"] = True
            state["package_ready"] = True

def activate_bottomservo_for_1kg():
    servo.angle = -90
    servo1.angle = 40
    state["bottom_gate_open"] = True

def deactivate_bottomservo():
    servo.angle = -30
    servo1.angle = -20
    state["bottom_gate_open"] = False
    state["sack_detected"] = False  # Ready for next detection
    print("[DEBUG] Bottom gate closed and sack detection reset.")


def reset_system():
    hx1.tare()
    hx2.tare()
    state["top_gate_open"] = False
    state["top_gate_closed"] = False
    state["waiting_for_reset"] = False
    state["package_ready"] = False

def stop_system():
    global state
    with servo_lock:
        if state["top_gate_open"]:
            print("[DEBUG] Closing top gate due to STOP")
            servo2.angle = -36
            servo3.angle = 26
            #state["top_gate_open"] = False
            #state["top_gate_closed"] = True
            time.sleep(1)

    # Clear LCD and show STOP message
    display.lcd_clear()
    time.sleep(0.1)
    display.lcd_display_string(center_text("   System Stopped"), 1)
    display.lcd_display_string(center_text("    Press START"), 2)
    GPIO.output(CONTROL_PIN, GPIO.LOW)  # <-- Disable Arduino logic

    GPIO.output(VIBRATOR1_PIN, GPIO.LOW)
    GPIO.output(VIBRATOR2_PIN, GPIO.LOW)

    # ? Reset the state so next START works as expected
    reset_system()

def initialize_system():
    hx1.reset()
    hx2.reset()
    hx1.tare()
    hx2.tare()
    display.lcd_clear()
    time.sleep(0.1)
    display.lcd_display_string(center_text("System Starting..."), 2)
    time.sleep(1)
    display.lcd_clear()
    display.lcd_display_string(center_text("    System Ready"), 2)
    time.sleep(1)
    display.lcd_clear()
    GPIO.output(CONTROL_PIN, GPIO.HIGH)

def listen_for_sack():
    if arduino:
        while arduino.in_waiting:
            line = arduino.readline().decode('utf-8').strip()
            print(f"[SERIAL] {line}")
            if "SACK_DETECTED" in line:
                print("[INFO] Sack detected via ultrasonic.")
                state["sack_detected"] = True  # Set flag
                # Only open gate if package is ready
                if state["package_ready"] and not state["bottom_gate_open"]:
                    time.sleep(2)
                    activate_bottomservo_for_1kg()

def finish_5kg():
    requests.put("http://127.0.0.1:5000/count/5kg")

# --- Main control function ---
def run_system():
    global should_run
    start_time = time.time()  # Record system start time

    try:
        while should_run:
            listen_for_sack()  # Listen for sack detection events

            weight1 = hx1.get_weight(10) / 1000
            weight2 = hx2.get_weight(10) / 1000
            weight1 = max(weight1, 0)
            weight2 = max(weight2, 0)
            total_weight = (weight1 + weight2) / 2
            rounded_weight = round(total_weight, 2)

            display.lcd_display_string(center_text("    Total Weight:"), 1)
            display.lcd_display_string(center_text(f"  {rounded_weight:>6.2f} kg"), 2)
            print(f"[DEBUG] Weight: {rounded_weight:.2f}, States: {state}")

            # Wait at least 1 seconds before allowing servo actions
            if time.time() - start_time > 1:
                # Open the top gate if weight is within the range and top gate isn't open
                if not state["top_gate_open"] and rounded_weight <= 0.03:
                    threading.Thread(target=activate_top_servo_open).start()

                # Close the top gate and open the bottom gate if weight is right and conditions met
                if state["top_gate_open"] and not state["top_gate_closed"] and 4.85 <= rounded_weight <= 5.20:
                    threading.Thread(target=activate_top_servo_close).start()

                # Debug for bottom gate opening
                if state["top_gate_closed"] and not state["bottom_gate_open"] and rounded_weight <= 4.85:
                    if state["sack_detected"]:  # Check if sack is detected
                        print("[INFO] Sack detected, opening bottom gate.")
                        threading.Thread(target=activate_bottomservo_for_1kg).start()
                        print(f"[DEBUG] Bottom gate opened, sack_detected: {state['sack_detected']}")
                    else:
                        print("[INFO] Sack not detected, waiting to open bottom gate.")
                        print(f"[DEBUG] Sack detected status: {state['sack_detected']}")

                # If bottom gate is open, reset system once weight drops
                if state["bottom_gate_open"] and rounded_weight <= 0.05:
                    threading.Thread(target=deactivate_bottomservo).start()
                    reset_system()
                    finish_5kg()

            time.sleep(0.2)

    except KeyboardInterrupt:
        display.lcd_clear()
        display.lcd_display_string("Program Stopped", 1)
        time.sleep(2)
        display.lcd_clear()