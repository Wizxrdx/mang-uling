import os
import pickle
from datetime import datetime
from pmdarima import auto_arima
from statsmodels.tsa.statespace.sarimax import SARIMAX
import pandas as pd

MODEL_PATH = "models"


def get_parameters(data, is_1kg=True):
    current_month = datetime.now().strftime("%Y-%m")
    if is_1kg:
        bag_type = '1_kg'
    else:
        bag_type = '10_kg'
    file_name = f"{bag_type}_{current_month}.pkl" # should be 1_kg_2025-02.pkl
    current_order_path = os.path.join(MODEL_PATH, file_name)

    if not os.path.isfile(current_order_path):
        # Create a new order file
        print("Order for this month does not exist. Creating a new one...")
        parameters = auto_arima(data, seasonal=True, m=7, stepwise=True)
        print(f"Order for {current_month} created.")
        # save the order file
        print(f"Saving order to '{file_name}'...")
        with open(current_order_path, "wb") as save_file:
            pickle.dump(parameters, save_file)
        print(f"File '{file_name}' created.")
    else:
        print(f"File '{file_name}' exists. loading the order...")
        # Load the existing order file
        with open(current_order_path, "rb") as saved_file:
            parameters = pickle.load(saved_file)

    return (parameters.order, parameters.seasonal_order)

def perform_forecast(order, seasonal_order, data, days=30):
    predictions = []

    for i in range(days):
        # Train a new SARIMA model using only the last 6 months
        rolling_model = SARIMAX(data, order=order, seasonal_order=seasonal_order).fit()
        
        # Predict the next day's sales
        forecast = rolling_model.forecast()
        predictions.append(round(forecast.values[0]))
        
        # Append forecasted value to history for the next iteration
        history = pd.concat([data, pd.Series(forecast.values[0], index=[data.index[i]])])

    # Store the forecasts in DataFrame
    return predictions