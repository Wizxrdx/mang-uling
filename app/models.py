from . import db
from datetime import datetime, timezone
from flask_bcrypt import generate_password_hash, check_password_hash

class BagType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), unique=True, nullable=False)

class DailyForecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    forecast_date = db.Column(db.String(10), nullable=False, default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    bag_type_id = db.Column(db.Integer, db.ForeignKey('bag_type.id', name='fk_daily_forecast_bag_type_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    change = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    bag_type = db.relationship('BagType', backref=db.backref('forecasts', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('forecast_date', 'bag_type_id', name='uq_daily_forecast_date_bag_type'),
    )

class DailyProduction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    production_date = db.Column(db.String(10), nullable=False, default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    bag_type_id = db.Column(db.Integer, db.ForeignKey('bag_type.id', name='fk_daily_production_bag_type_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    bag_type = db.relationship('BagType', backref=db.backref('productions', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('production_date', 'bag_type_id', name='uq_daily_production_date_bag_type'),
    )

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)