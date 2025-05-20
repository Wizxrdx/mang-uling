from datetime import datetime, timedelta
import calendar
import pandas as pd


def get_first_day_of_iso_week(year, week_num):
    # Get a date object for the first day of the given ISO week
    # isocalendar() gives (ISO year, ISO week number, ISO weekday)
    first_day_of_week = datetime(year, 1, 1)
    first_day_of_week = first_day_of_week - timedelta(days=first_day_of_week.weekday())  # Move to the first Monday
    
    # Now move to the correct ISO week
    days_to_add = (week_num - 1) * 7  # Move to the desired week number
    first_day_of_week += timedelta(days=days_to_add)

    return first_day_of_week

def get_readable_week_of_month(year, week_num):
    # Calculate the first day of the ISO week (Monday)
    first_day_of_week = get_first_day_of_iso_week(year, week_num)

    # Start of the week (Monday)
    start_of_week = first_day_of_week
    
    # End of the week (Sunday)
    end_of_week = start_of_week + timedelta(days=6)
    
    # Format the readable range (e.g., "Jan 1 – Jan 7")
    readable_week = f"{start_of_week.strftime('%b %d')} - {end_of_week.strftime('%b %d')}"
    
    return readable_week

def get_days_in_month():
    today = datetime.today()
    _, days = calendar.monthrange(today.year, today.month)
    
    return (today.replace(day=1), days)


def data_to_dataframe(results):
    data = {}
    for date, bag_type, quantity in results:
        if date not in data:
            data[date] = {"quantity_1kg": 0, "quantity_5kg": 0}
        if bag_type == "1kg":
            data[date]["quantity_1kg"] = quantity
        elif bag_type == "5kg":
            data[date]["quantity_5kg"] = quantity

    # Create DataFrame
    df = pd.DataFrame([
        {"production_date": date, **vals} for date, vals in data.items()
    ]).sort_values("production_date")

    return df