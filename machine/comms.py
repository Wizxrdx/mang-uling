import requests
from machine.main_button import Machine
import machine.servo_and_loadcell_1kg as system_1kg
import machine.servo_and_loadcell_5kg as system_5kg

def start_1kg():
    Machine().change_system(system_1kg)

def start_5kg():
    Machine().change_system(system_5kg)

def reset_system():
    Machine().reset_system()
