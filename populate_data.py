from app import create_app, db
from app.models import Employee, BagType, DailyProduction
from datetime import datetime, timedelta

app = create_app()

# Monthly data
data = {
    "2024-08": {"1kg": 777, "10kg": 780, "days": 31},
    "2024-09": {"1kg": 385, "10kg": 885, "days": 30},
    "2024-10": {"1kg": 385, "10kg": 885, "days": 31},
    "2024-11": {"1kg": 240, "10kg": 1010, "days": 30},
    "2024-12": {"1kg": 450, "10kg": 740, "days": 31},
}

with app.app_context():
    # Create bag types  
    one_kg_bag = BagType(type="1kg")
    ten_kg_bag = BagType(type="10kg")

    db.session.add(one_kg_bag)
    db.session.add(ten_kg_bag)
    db.session.commit()
    print("Bag types added successfully!")

    bag_types = {bt.type: bt.id for bt in BagType.query.all()}
    print(bag_types)

    for month, details in data.items():
        year, month_num = map(int, month.split("-"))
        start_date = datetime(year, month_num, 1)
        
        for day in range(details["days"]):
            date = (start_date + timedelta(days=day)).strftime("%Y-%m-%d")
            for bag_type, total_kg in details.items():
                if bag_type in ["days"]: continue
                daily_quantity = total_kg // details["days"]

                entry = DailyProduction(
                    production_date=date,
                    bag_type_id=bag_types[bag_type],
                    quantity=daily_quantity
                )
                db.session.add(entry)
    db.session.commit()
    print("Monthly data added successfully!")

    employee = Employee(name="John Doe", username="johndoe")
    employee.set_password("securepassword")

    db.session.add(employee)
    db.session.commit()
    print("Employee added successfully!")
