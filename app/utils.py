from datetime import datetime, timedelta
import calendar

def get_readable_week_of_month(year, week_num):
    # Calculate the first day of the week (Monday)
    first_day_of_week = datetime.strptime(f'{year}-W{week_num}-1', "%Y-W%W-%w")

    # Start of the week (Monday)
    start_of_week = first_day_of_week
    
    # End of the week (Sunday)
    end_of_week = start_of_week + timedelta(days=6)
    
    # Get the month name and format the result
    month_name = start_of_week.strftime("%B")
    
    # Format the readable range (e.g., "Jan 1 – Jan 7")
    readable_week = f"{start_of_week.strftime('%b %d')} - {end_of_week.strftime('%b %d')}"
    
    return readable_week