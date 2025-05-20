import os
import pickle
from datetime import datetime
from pmdarima import auto_arima
from statsmodels.tsa.statespace.sarimax import SARIMAX
import pandas as pd

from app import utils

MODEL_PATH = "parameters"
FORECAST_DAYS_1KG = 60
FORECAST_DAYS_10KG = 60


def is_new_month():
    """Check if the current month is new by checking if the file for the current month exists."""
    current_month = datetime.now().strftime("%Y-%m")
    file_name = f"1kg_{current_month}.pkl" # should be 1_kg_2025-02.pkl
    current_order_path = os.path.join(MODEL_PATH, file_name)

    return not os.path.isfile(current_order_path)

def create_monthly_forecast(data):
    """Create a monthly forecast for 1kg and 10kg bags."""
    data_df = utils.data_to_dataframe(data)
    data_df['production_date'] = pd.to_datetime(data_df['production_date'])
    data_df.set_index('production_date', inplace=True)
    data_1kg = data_df.drop(['quantity_5kg'], axis=1)
    data_10kg = data_df.drop(['quantity_1kg'], axis=1)

    order_1kg, seasonal_order_1kg, order_10kg, seasonal_order_10kg = get_parameters(data_1kg, data_10kg)
    first_day, days_in_month = utils.get_days_in_month()

    forecast_1kg = perform_forecast(order_1kg, seasonal_order_1kg, data_1kg, start_date=first_day, days=days_in_month, forecast_days=FORECAST_DAYS_1KG)
    forecast_10kg = perform_forecast(order_10kg, seasonal_order_10kg, data_10kg, start_date=first_day, days=days_in_month, forecast_days=FORECAST_DAYS_10KG)

    return (forecast_1kg, forecast_10kg)

def get_parameters(data_1kg, data_10kg):
    current_month = datetime.now().strftime("%Y-%m")

    if is_new_month():
        print("Orders for this month does not exist. Creating a new one...")
        # Delete all old order file if it exists
        for file in os.listdir(MODEL_PATH):
            if file.endswith(".pkl"):
                os.remove(os.path.join(MODEL_PATH, file))
                print(f"Deleted old order file: {file}")
        
        # Create a new 1kg order file
        parameters_1kg = auto_arima(data_1kg, seasonal=True, m=30, stepwise=True)
        print(f"Order for {current_month} created.")

        # save the order file
        file_name = f"1kg_{current_month}.pkl" # should be 1_kg_2025-02.pkl
        print(f"Saving order to '{file_name}'...")
        with open(os.path.join(MODEL_PATH, file_name), "wb") as save_file:
            pickle.dump(parameters_1kg, save_file)
        print(f"File '{file_name}' created.")

        # Create a new 10kg order file
        parameters_10kg = auto_arima(data_10kg, seasonal=True, m=30, stepwise=True)
        print(f"Order for {current_month} created.")

        # save the order file
        file_name = f"10kg_{current_month}.pkl" # should be 10_kg_2025-02.pkl
        print(f"Saving order to '{file_name}'...")
        with open(os.path.join(MODEL_PATH, file_name), "wb") as save_file:
            pickle.dump(parameters_10kg, save_file)
        print(f"File '{file_name}' created.")
    else:
        print(f"File '{file_name}' exists. loading the order...")
        # Load the existing 1kg order file
        file_name = f"1kg_{current_month}.pkl" # should be 10_kg_2025-02.pkl
        with open(os.path.join(MODEL_PATH, file_name), "rb") as saved_file:
            parameters_1kg = pickle.load(saved_file)

        # Load the existing 10kg order file
        file_name = f"10kg_{current_month}.pkl" # should be 10_kg_2025-02.pkl
        with open(os.path.join(MODEL_PATH, file_name), "rb") as saved_file:
            parameters_10kg = pickle.load(saved_file)

    return (parameters_1kg.order, parameters_1kg.seasonal_order, parameters_10kg.order, parameters_10kg.seasonal_order)

def perform_forecast(order, seasonal_order, data, start_date, days=30, forecast_days=60):
    forecast_df = pd.DataFrame(index=pd.date_range(start_date, periods=days, freq="D"))
    history = data[-forecast_days:]  # Use last 60 days for training
    predictions = []

    for i in range(days):
        model = SARIMAX(history, order=order, seasonal_order=seasonal_order).fit()
        forecast = model.forecast()
        predictions.append(round(forecast.values[0]))

        # Use the first column name from data if it has only one column
        column_name = data.columns[0]
        
        # Ensure we add the forecast value as a Series with the correct name and index
        forecast_series = pd.Series(forecast.values[0], index=[forecast_df.index[i]], name=column_name)
        history = pd.concat([history, forecast_series])

    forecast_df["forecast"] = predictions
    return forecast_df
