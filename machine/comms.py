import requests
from main_button import Machine
import servo_and_loadcell_1kg as system_1kg

def start_1kg():
    Machine().change_system(system_1kg)

def start_10kg():
    # Machine().change_system("10kg")
    pass

def finish_1kg():
    requests.put("http://127.0.0.1:5000/count/1kg")

def finish_10kg():
    requests.put("http://127.0.0.1:5000/count/10kg")
