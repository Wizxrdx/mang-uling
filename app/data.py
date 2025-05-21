import threading
from datetime import datetime, timedelta

import warnings

from machine.comms import reset_system, start_5kg, start_1kg
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

from sqlalchemy import func
from .models import BagType, DailyProduction, DailyForecast
from . import db
from forecasting import create_monthly_forecast, is_order_file_exists

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
                "5kg": {"size": 5, "count": 0, "quota": 0},
            }
            self.WEEKLY_LOG = {}
            self.TODAY = datetime.today()
            self.NOTIFY = False
            self.NOTIFY_MSG = None
            self.initialized = True

    def get_weekly_log(self):
        with self._lock:
            self.WEEKLY_LOG[self.TODAY.strftime("%Y-%m-%d")] = {
                "bag_1kg": self.DATA["1kg"]["count"],
                "bag_5kg": self.DATA["5kg"]["count"]
            }

            return self.WEEKLY_LOG

    def set_notification(self, msg):
        self.NOTIFY = True
        self.NOTIFY_MSG = msg

    def clear_notification(self):
        self.NOTIFY = False
        self.NOTIFY_MSG = None

    def check_notification(self):
        return self.NOTIFY
    
    def get_notification(self):
        with self._lock:
            msg = self.NOTIFY_MSG
            self.clear_notification()
            return msg

    def initialize_data(self):
        self.IS_BUSY = False

        if not is_order_file_exists("1kg"):
            print("New month detected for 1kg. Generating new forecast data.")
            data = get_production_record()
            forecast_1kg = create_monthly_forecast(data, "1kg")
            create_forecast_record(forecast_1kg, "1kg")

        if not is_order_file_exists("5kg"):
            print("New month detected for 5kg. Generating new forecast data.")
            data = get_production_record()
            forecast_5kg = create_monthly_forecast(data, "5kg")
            create_forecast_record(forecast_5kg, "5kg")

        last_daily_production_date = DailyProduction.query.order_by(DailyProduction.production_date.desc()).first().production_date
        create_production_record(self.TODAY, last_daily_production_date)

        start_of_week = self.TODAY - timedelta(days=self.TODAY.weekday())  # Monday of current week
        end_of_week = start_of_week + timedelta(days=6)  # Sunday of current week

        weekly_data = DailyProduction.query.filter(DailyProduction.production_date.between(start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d"))).all()
        for entry in weekly_data:
            if entry.production_date not in self.WEEKLY_LOG:
                self.WEEKLY_LOG[entry.production_date] = {"bag_1kg": 0, "bag_5kg": 0}

            if entry.bag_type_id == 1:
                self.WEEKLY_LOG[entry.production_date]["bag_1kg"] = entry.quantity
            else:
                self.WEEKLY_LOG[entry.production_date]["bag_5kg"] = entry.quantity

        forecasted_data_1kg_entry = get_forecast_record(self.TODAY.strftime("%Y-%m-%d"), bag_type="1kg")
        forecasted_data_5kg_entry = get_forecast_record(self.TODAY.strftime("%Y-%m-%d"), bag_type="5kg")

        forecasted_data_1kg = 1 if forecasted_data_1kg_entry.quantity == 0 else forecasted_data_1kg_entry.quantity
        final_data_1kg = forecasted_data_1kg if forecasted_data_1kg_entry.change is None else forecasted_data_1kg_entry.change
        forecasted_data_5kg = 1 if forecasted_data_5kg_entry.quantity == 0 else forecasted_data_5kg_entry.quantity
        final_data_5kg = forecasted_data_5kg if forecasted_data_5kg_entry.change is None else forecasted_data_5kg_entry.change

        today_data = self.WEEKLY_LOG[self.TODAY.strftime("%Y-%m-%d")]
        self.DATA = {
            "1kg": {"size": 1, "count": today_data['bag_1kg'], "quota": int(final_data_1kg)},
            "5kg": {"size": 5, "count": today_data['bag_5kg'], "quota": int(final_data_5kg)},
        }

        self.auto_start()
        print("Global variables initialized successfully.")

    def start(self, bag):
        with self._lock:
            self.IS_BUSY = bag if bag in ["1kg", "5kg"] else False
            if self.IS_BUSY == "1kg":
                start_1kg()
                pass
            elif self.IS_BUSY == "5kg":
                start_5kg()
                pass
            else:
                pass
                reset_system()

        return True
    
    def get_is_busy(self):
        with self._lock:
            return self.IS_BUSY

    def auto_start(self):
        if self.DATA["1kg"]["count"] < self.DATA["1kg"]["quota"]:
            self.start("1kg")
        elif self.DATA["5kg"]["count"] < self.DATA["5kg"]["quota"]:
            self.start("5kg")
        else:
            self.start(None)

    def update_quota(self, date, bag_type, quantity):
        bag_type_id = BagType.query.filter_by(type=bag_type).first().id
        self.DATA[bag_type]["quota"] = quantity
        # Check if the quota already exists for the given date and bag type
        existing_quota = DailyForecast.query.filter_by(forecast_date=date.strftime('%Y-%m-%d'), bag_type_id=bag_type_id).first()
        if existing_quota:
            # Update the existing quota record
            existing_quota.change = quantity
        else:
            # Create a new quota record
            quota = DailyForecast(
                forecast_date=date.strftime('%Y-%m-%d'),
                bag_type_id=bag_type_id,
                quantity=0,
                change=quantity
            )

            db.session.add(quota)
        db.session.commit()


    def update_production_record(self, size, quantity):
        self.DATA[size]["count"] += quantity
        # DailyProduction.query.filter_by(production_date=TODAY.strftime("%Y-%m-%d"), bag_type_id=BagType.query.filter_by(type=bag_type).first().id).update({"quantity": DATA[bag_type]["count"]})
        bag_type = BagType.query.filter_by(type=size).first().id
        record = DailyProduction.query.filter_by(production_date=self.TODAY.strftime("%Y-%m-%d"), bag_type_id=bag_type).first()
        record.quantity = self.DATA[size]["count"]
        db.session.commit()

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

def create_forecast_record(data, prefix):
    # 1kg data
    bag_types = {bt.type: bt.id for bt in BagType.query.all()}

    for date, row in data.iterrows():
        quantity = 0 if int(row['forecast']) < 1 else int(row['forecast'])
        forecast_date = date.strftime('%Y-%m-%d')
        bag_type_id = bag_types[prefix]
        
        # Check if record exists
        existing_forecast = DailyForecast.query.filter_by(
            forecast_date=forecast_date,
            bag_type_id=bag_type_id
        ).first()
        
        if existing_forecast:
            # Update existing record
            existing_forecast.quantity = quantity
        else:
            # Create new record
            forecast = DailyForecast(
                forecast_date=forecast_date,
                bag_type_id=bag_type_id,
                quantity=quantity
            )
            db.session.add(forecast)

    db.session.commit()

def get_forecast_record(date, bag_type):
    bag = BagType.query.filter_by(type=bag_type).first().id if bag_type in ["1kg", "5kg"] else None
    if date is not None and bag is not None:
        return DailyForecast.query.filter_by(forecast_date=date, bag_type_id=bag).first()
