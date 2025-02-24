import os
import pickle
from datetime import datetime
from pmdarima import auto_arima
from statsmodels.tsa.statespace.sarimax import SARIMAX

MODEL_PATH = "models"


def get_order(data):
    current_month = datetime.now().strftime("%Y-%m")
    file_name = f"{current_month}.pkl" # should be 2025-02.pkl
    current_order_path = os.path.join(MODEL_PATH, file_name)

    if not os.path.isfile(current_order_path):
        # Create a new order file
        print("Order for this month does not exist. Creating a new one...")
        order = auto_arima(data, seasonal=True, m=7, stepwise=True)
        print(f"Order for {current_month} created.")
        # save the order file
        print(f"Saving order to '{file_name}'...")
        with open(current_order_path, "w") as file:
            pickle.dump(order, file)
        print(f"File '{file_name}' created.")
    else:
        print(f"File '{file_name}' exists. loading the order...")
        # Load the existing order file
        with open(current_order_path, "r") as file:
            order_data = pickle.load(file)

    return order

def create_arima_model(data):
    # Create the ARIMA model
    model = SARIMAX(data, order=(5,1,0))
    
    # Fit the model
    model_fit = model.fit(disp=0)
    
    return model_fit


if __name__ == "__main__":
    get_order("data")