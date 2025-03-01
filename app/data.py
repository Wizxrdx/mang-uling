import threading
from datetime import datetime, timedelta

from .models import BagType, DailyProduction
from . import db

lock = threading.Lock()

IS_BUSY = False
DATA = {
    "1kg": {"size": 1, "count": 0, "quota": 0},
    "10kg": {"size": 10, "count": 0, "quota": 0},
}
WEEKLY_LOG = {}
TODAY = datetime.today()

def initialize_data():
    global DATA, IS_BUSY, WEEKLY_LOG, TODAY
    IS_BUSY = False

    # there might be days without any production
    last_daily_production_date = DailyProduction.query.order_by(DailyProduction.production_date.desc()).first().production_date
    create_production_record(TODAY, last_daily_production_date)

    # fetch weekly log data
    start_of_week = TODAY - timedelta(days=TODAY.weekday())  # Monday of current week
    end_of_week = start_of_week + timedelta(days=6)  # Sunday of current week

    weekly_data = DailyProduction.query.filter(DailyProduction.production_date.between(start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d"))).all()
    for entry in weekly_data:
        if entry.production_date not in WEEKLY_LOG:
            WEEKLY_LOG[entry.production_date] = {"bag_1kg": 0, "bag_10kg": 0}

        if entry.bag_type_id == 1:
            WEEKLY_LOG[entry.production_date]["bag_1kg"] = entry.quantity
        else:
            WEEKLY_LOG[entry.production_date]["bag_10kg"] = entry.quantity

    # fetch forecasted data for and add as quota
    today_data = WEEKLY_LOG[TODAY.strftime("%Y-%m-%d")]
    DATA = {
        "1kg": {"size": 1, "count": today_data['bag_1kg'], "quota": 10},
        "10kg": {"size": 10, "count": today_data['bag_10kg'], "quota": 5},
    }

    print("Global variables initialized successfully.")

def create_production_record(date, start_date=None):
    bag_types = {bt.type: bt.id for bt in BagType.query.all()}

    if start_date is None:
        for bag_type in bag_types.values():
            record = DailyProduction(production_date=date, bag_type_id=bag_type, quantity=0)
            db.session.add(record)
    else:
        # generate data from start_date to date
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(date.strftime("%Y-%m-%d"), "%Y-%m-%d")

        while current_date < end_date:
            current_date += timedelta(days=1)
            for bag_type in bag_types.values():
                record = DailyProduction(production_date=current_date.strftime("%Y-%m-%d"), bag_type_id=bag_type, quantity=0)
                db.session.add(record)

    db.session.commit()

def update_production_record(size, quantity):
    global TODAY, DATA
    DATA[size]["count"] += quantity
    # DailyProduction.query.filter_by(production_date=TODAY.strftime("%Y-%m-%d"), bag_type_id=BagType.query.filter_by(type=bag_type).first().id).update({"quantity": DATA[bag_type]["count"]})
    bag_type = BagType.query.filter_by(type=size).first().id
    record = DailyProduction.query.filter_by(production_date=TODAY.strftime("%Y-%m-%d"), bag_type_id=bag_type).first()
    record.quantity = DATA[size]["count"]
    db.session.commit()