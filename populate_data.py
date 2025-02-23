from app.models import Employee, BagType, DailyProduction
from datetime import datetime, timedelta
import numpy as np

# Monthly data
data = {
    "2024-08": {"1kg": 777, "10kg": 780, "days": 31},
    "2024-09": {"1kg": 385, "10kg": 885, "days": 30},
    "2024-10": {"1kg": 385, "10kg": 885, "days": 31},
    "2024-11": {"1kg": 240, "10kg": 1010, "days": 30},
    "2024-12": {"1kg": 450, "10kg": 740, "days": 31},
}

def populate_data(db):
    # Create bag types  
    one_kg_bag = BagType(type="1kg")
    ten_kg_bag = BagType(type="10kg")

    db.session.add(one_kg_bag)
    db.session.add(ten_kg_bag)
    db.session.commit()
    print("Bag types added successfully!")

    bag_types = {bt.type: bt.id for bt in BagType.query.all()}

    for month, details in data.items():
        year, month_num = map(int, month.split("-"))
        start_date = datetime(year, month_num, 1)
        days_in_month = details["days"]

        for bag_type, total_kg in details.items():
            if bag_type == "days":
                continue

            # Generate random daily sales while keeping the total monthly sales accurate
            mean_daily = total_kg / days_in_month
            daily_sales = np.random.normal(loc=mean_daily, scale=mean_daily * 0.3, size=days_in_month)
            daily_sales = np.round(daily_sales).astype(int)

            # Ensure no negative values
            daily_sales = np.maximum(daily_sales, 0)

            # Adjust last day to match total sales
            daily_sales[-1] += total_kg - daily_sales.sum()

            for day in range(days_in_month):
                date = (start_date + timedelta(days=day)).strftime("%Y-%m-%d")
                entry = DailyProduction(
                    production_date=date,
                    bag_type_id=bag_types[bag_type],
                    quantity=int(daily_sales[day])
                )
                db.session.add(entry)

    db.session.commit()
    print("Monthly data added successfully!")

    # Add an employee
    employee = Employee(name="John Doe", username="johndoe")
    employee.set_password("securepassword")

    db.session.add(employee)
    db.session.commit()
    print("Employee added successfully!")
