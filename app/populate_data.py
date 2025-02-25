import random
from app.models import Employee, BagType, DailyProduction
from datetime import datetime, timedelta

# Monthly data
data = {
    "2024-08": {"1kg": 777, "10kg": 780, "days": 31},
    "2024-09": {"1kg": 385, "10kg": 885, "days": 30},
    "2024-10": {"1kg": 385, "10kg": 885, "days": 31},
    "2024-11": {"1kg": 240, "10kg": 1010, "days": 30},
    "2024-12": {"1kg": 450, "10kg": 740, "days": 31},
}

def generate_randomized_sales(total_kg, days):
    """Generate random daily sales ensuring the sum matches total_kg."""
    sales = []
    remaining_kg = total_kg

    for _ in range(days - 1):
        daily = max(0, int(random.uniform(0.7, 1.3) * (total_kg / days)))
        sales.append(daily)
        remaining_kg -= daily

    # Ensure the last day adjusts to match total_kg
    sales.append(max(0, remaining_kg))
    return sales

def populate_bag_types(db):
    # Create bag types  
    one_kg_bag = BagType(type="1kg")
    ten_kg_bag = BagType(type="10kg")

    db.session.add(one_kg_bag)
    db.session.add(ten_kg_bag)
    db.session.commit()
    print("Bag types added successfully!")

def populate_credentials(db):
    # Add an employee
    employee = Employee(name="Admin", username="admin")
    employee.set_password("1234")

    db.session.add(employee)
    db.session.commit()
    print("Employee added successfully!")

def populate_with_real_data(db):
    bag_types = {bt.type: bt.id for bt in BagType.query.all()}

    for month, details in data.items():
        year, month_num = map(int, month.split("-"))
        start_date = datetime(year, month_num, 1)
        days_in_month = details["days"]

        for bag_type, total_kg in details.items():
            if bag_type == "days":
                continue

            # Generate random daily sales
            daily_sales = generate_randomized_sales(total_kg, days_in_month)

            for day in range(days_in_month):
                date = (start_date + timedelta(days=day)).strftime("%Y-%m-%d")
                entry = DailyProduction(
                    production_date=date,
                    bag_type_id=bag_types[bag_type],
                    quantity=daily_sales[day]
                )
                db.session.add(entry)

    db.session.commit()
    print("Monthly data added successfully!")

def populate_with_fake_data(db, start_date="2025-01-01"):
    bag_types = {bt.type: bt.id for bt in BagType.query.all()}
    
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.now()
    days = (end_date - start_date).days

    entries = []
    for day in range(days + 1):  # Loop from start_date to today
        current_date = (start_date + timedelta(days=day)).strftime("%Y-%m-%d")
        for bag_type_id in bag_types.values():
            entry = DailyProduction(
                production_date=current_date,
                bag_type_id=bag_type_id,
                quantity=random.randint(100, 1000)
            )
            entries.append(entry)

    db.session.bulk_save_objects(entries)
    db.session.commit()
    print("Fake data added successfully!")