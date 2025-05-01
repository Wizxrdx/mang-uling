import threading
from datetime import datetime, timedelta

from sqlalchemy import func
from .models import BagType, DailyProduction, DailyForecast
from . import db
from forecasting import create_monthly_forecast, is_new_month

class State:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(State, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # Ensure initialization happens only once
            self.IS_BUSY = "1kg"
            self.DATA = {
                "1kg": {"size": 1, "count": 0, "quota": 0},
                "10kg": {"size": 10, "count": 0, "quota": 0},
            }
            self.WEEKLY_LOG = {}
            self.TODAY = datetime.today()
            self.initialized = True  # Mark as initialized

    def initialize_data(self):
        self.IS_BUSY = False
        if is_new_month():
            data = get_production_record()
            forecast_1kg, forecast_10kg = create_monthly_forecast(data)
            create_forecast_record(forecast_1kg, forecast_10kg)

        last_daily_production_date = DailyProduction.query.order_by(DailyProduction.production_date.desc()).first().production_date
        create_production_record(self.TODAY, last_daily_production_date)

        start_of_week = self.TODAY - timedelta(days=self.TODAY.weekday())  # Monday of current week
        end_of_week = start_of_week + timedelta(days=6)  # Sunday of current week

        weekly_data = DailyProduction.query.filter(DailyProduction.production_date.between(start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d"))).all()
        for entry in weekly_data:
            if entry.production_date not in self.WEEKLY_LOG:
                self.WEEKLY_LOG[entry.production_date] = {"bag_1kg": 0, "bag_10kg": 0}

            if entry.bag_type_id == 1:
                self.WEEKLY_LOG[entry.production_date]["bag_1kg"] = entry.quantity
            else:
                self.WEEKLY_LOG[entry.production_date]["bag_10kg"] = entry.quantity

        forecasted_data_1kg_entry = get_forecast_record(self.TODAY.strftime("%Y-%m-%d"), bag=0)
        forecasted_data_10kg_entry = get_forecast_record(self.TODAY.strftime("%Y-%m-%d"), bag=1)
        forecasted_data_1kg = 1 if forecasted_data_1kg_entry.quantity == 0 else forecasted_data_1kg_entry.quantity
        forecasted_data_10kg = 1 if forecasted_data_10kg_entry.quantity == 0 else forecasted_data_10kg_entry.quantity

        today_data = self.WEEKLY_LOG[self.TODAY.strftime("%Y-%m-%d")]
        self.DATA = {
            "1kg": {"size": 1, "count": today_data['bag_1kg'], "quota": int(forecasted_data_1kg)},
            "10kg": {"size": 10, "count": today_data['bag_10kg'], "quota": int(forecasted_data_10kg)},
        }

        self.auto_start()
        print("Global variables initialized successfully.")

    def start(self, bag):
        with State._lock:
            self.IS_BUSY = bag if bag in ["1kg", "10kg"] else False
        return True
    
    def get_is_busy(self):
        with State._lock:
            return self.IS_BUSY

    def auto_start(self):
        if self.DATA["1kg"]["count"] < self.DATA["1kg"]["quota"]:
            self.start("1kg")
        elif self.DATA["10kg"]["count"] < self.DATA["10kg"]["quota"]:
            self.start("10kg")
        else:
            self.start(None)

    def update_production_record(self, size, quantity):
        global TODAY, DATA, WEEKLY_LOG
        self.DATA[size]["count"] += quantity
        # DailyProduction.query.filter_by(production_date=TODAY.strftime("%Y-%m-%d"), bag_type_id=BagType.query.filter_by(type=bag_type).first().id).update({"quantity": DATA[bag_type]["count"]})
        bag_type = BagType.query.filter_by(type=size).first().id
        record = DailyProduction.query.filter_by(production_date=self.TODAY.strftime("%Y-%m-%d"), bag_type_id=bag_type).first()
        record.quantity = self.DATA[size]["count"]
        db.session.commit()

# app/state.py (continued)

def get_production_record(start_date=None, end_date=None):
    query = db.session.query(
        DailyProduction.production_date,
        BagType.type,
        func.sum(DailyProduction.quantity).label("total_quantity")
    ).join(BagType)

    if start_date and end_date:
        query = query.filter(DailyProduction.production_date.between(start_date, end_date))

    query = query.group_by(DailyProduction.production_date, BagType.type)

    return query.all()

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

def create_forecast_record(data_1kg, data_10kg):
    # 1kg data
    for date, row in data_1kg.iterrows():
        quantity = 0 if int(row['forecast']) < 1 else int(row['forecast'])
        forecast = DailyForecast(
            forecast_date=date.strftime('%Y-%m-%d'),
            bag_type_id=0,
            quantity=quantity
        )
        db.session.add(forecast)

    # 10kg data
    for date, row in data_10kg.iterrows():
        quantity = 0 if int(row['forecast']) < 1 else int(row['forecast'])
        forecast = DailyForecast(
            forecast_date=date.strftime('%Y-%m-%d'),
            bag_type_id=1,
            quantity=quantity
        )
        db.session.add(forecast)

    db.session.commit()

def get_forecast_record(date, bag):
    if date is not None and bag is not None:
        return DailyForecast.query.filter_by(forecast_date=date, bag_type_id=bag).first()
