import threading
import time
from gpiozero import Button
import RPi.GPIO as GPIO

class Machine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Machine, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        self.system = None
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.start_button = Button(17, pull_up=True, bounce_time=0.05)
        self.stop_button = Button(16, pull_up=True, bounce_time=0.05)

        self.system_thread = None

        # Start listening thread
        threading.Thread(target=self.listen_for_buttons, daemon=True).start()

    def change_system(self, system):
        if self.system is not None:
            self.stop_pressed()
        self.system = system
        self.system_thread = None

    def reset_system(self):
        if self.system is not None:
            self.stop_pressed()
        self.system = None
        self.system_thread = None

    def start_pressed(self):
        if self.system is None:
            print("No system selected.")
            return
        
        if self.system_thread is None or not self.system_thread.is_alive():
            print("START button pressed!")
            self.system.should_run = True
            self.system.initialize_system()
            print("Starting system thread...")
            self.system_thread = threading.Thread(target=self.system.run_system)
            self.system_thread.start()
        else:
            print("System already running.")

    def stop_pressed(self):
        if self.system is None:
            print("No system selected.")
            return
        
        print("STOP button pressed!")
        self.system.should_run = False
        self.system.stop_system()

    def listen_for_buttons(self):
        self.start_button.when_pressed = self.start_pressed
        self.stop_button.when_pressed = self.stop_pressed

        print("Waiting for START/STOP button press...")

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Exiting program...")
        finally:
            GPIO.cleanup()
