import threading
from .models import DailyProduction
from datetime import datetime, timedelta

lock = threading.Lock()

IS_BUSY = False
DATA = {
    "1kg": {"size": 1, "count": 0, "quota": 100},
    "10kg": {"size": 10, "count": 0, "quota": 50},
}
WEEKLY_LOG = {}
TODAY = datetime.today()

def initialize_data():
    global DATA, IS_BUSY, WEEKLY_LOG, TODAY
    IS_BUSY = False

    # fetch forecasted data for and add as quota
    DATA = {
        "1kg": {"size": 1, "count": 0, "quota": 100},
        "10kg": {"size": 10, "count": 0, "quota": 50},
    }

    # fetch weekly log data
    start_of_week = TODAY - timedelta(days=TODAY.weekday())  # Monday of current week
    end_of_week = start_of_week + timedelta(days=6)  # Sunday of current week

    weekly_data = DailyProduction.query.filter(DailyProduction.production_date.between(start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d"))).all()
    for entry in weekly_data:
        WEEKLY_LOG[entry.production_date] = {
            "bag_1kg": entry.quantity,
            "bag_10kg": entry.quantity
        }

    print("Global variables initialized successfully.")