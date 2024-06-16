import _thread
import json
import logging
import os
import threading
from datetime import datetime

import numpy as np
import websocket
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model

from config import Config

# Set environment variable to turn off oneDNN optimizations
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levellevelname)s - %(message)s", level=logging.INFO
)

# Load configuration
config = Config()

# Load the GRU model
model = load_model(config.model_path)
scaler = MinMaxScaler(feature_range=(0, 1))

# Initialize variables
last_closing_prices = []
last_predicted_price = None
last_candle_data = None
successful_predictions = 0
unsuccessful_predictions = 0
window_size = config.get("window_size", 14)

logging.info("Initialization complete.")


class SocketConn(websocket.WebSocketApp):
    def __init__(self, url, params=[]):
        super().__init__(url=url, on_open=self.on_open)
        self.params = params
        self.on_message = self.message
        self.on_error = self.error
        self.on_close = self.close
        self.last_kline_timestamp = None
        self.thread = threading.Thread(target=self.run_forever)
        self.thread.start()

    def on_open(self, ws):
        logging.info("WebSocket connection opened.")

        def run(*args):
            trade_str = {"op": "subscribe", "args": self.params}
            ws.send(json.dumps(trade_str))

        _thread.start_new_thread(run, ())

    def message(self, ws, msg):
        global last_candle_data, successful_predictions, unsuccessful_predictions

        try:
            data = json.loads(msg)
            if "topic" in data and data["topic"].startswith("kline"):
                kline_info = data["data"][0]
                close_price = float(kline_info["close"])
                end_timestamp = kline_info["end"]

                last_candle_data = kline_info  # Save last candle data

                if self.last_kline_timestamp != end_timestamp:
                    self.last_kline_timestamp = end_timestamp

                    last_closing_prices.append(close_price)

                    if len(last_closing_prices) > window_size:
                        last_closing_prices.pop(0)

                    logging.info(f"Accumulated closing prices: {len(last_closing_prices)}/{window_size}")

                    if len(last_closing_prices) == window_size:
                        self.predict_next_candle()

                    start_timestamp = kline_info["start"]
                    start_str = datetime.fromtimestamp(start_timestamp / 1000).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    end_str = datetime.fromtimestamp(end_timestamp / 1000).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    logging.info(
                        f"""Криптовалюта: {symbol}, Интервал: {kline_info['interval']} min
                    Данные свечи:
                    Start: {start_str}, End: {end_str}
                    Open: {kline_info['open']}, Close: {close_price}
                    High: {kline_info['high']}, Low: {kline_info['low']}
                    Volume: {kline_info['volume']}, Turnover: {kline_info['turnover']}
                    """
                    )
        except Exception as e:
            logging.error(f"Error in message processing: {e}")

    def error(self, ws, e):
        logging.error(f"WebSocket error: {e}")

    def close(self, ws):
        logging.info("WebSocket connection closed.")

    def predict_next_candle(self):
        global last_predicted_price, successful_predictions, unsuccessful_predictions
        try:
            last_prices = np.array(last_closing_prices).reshape(-1, 1)
            scaled_data = scaler.fit_transform(last_prices)
            X_test = np.reshape(scaled_data, (1, scaled_data.shape[0], 1))
            predicted_price = model.predict(X_test)
            last_predicted_price = scaler.inverse_transform(predicted_price)[0][0]
            logging.info(f"Прогнозируемая цена: {last_predicted_price}")

            if last_predicted_price and last_closing_prices:
                current_price = last_closing_prices[-1]
                previous_price = last_closing_prices[-2]
                difference = last_predicted_price - current_price
                difference_percentage = (difference / current_price) * 100
                prediction = "вырастет 📈" if difference > 0 else "упадет 📉"
                logging.info(
                    f"Текущая цена: {current_price}, Прогнозируемая цена: {last_predicted_price}"
                )
                logging.info(
                    f"Разница: {difference}, Разница в процентах: {difference_percentage:.2f}%, Прогноз: Цена {prediction}"
                )

                if (difference > 0 and current_price > previous_price) or (
                    difference < 0 and current_price < previous_price
                ):
                    successful_predictions += 1
                else:
                    unsuccessful_predictions += 1
                logging.info(
                    f"Updated statistics - Successful: {successful_predictions}, Unsuccessful: {unsuccessful_predictions}"
                )
        except Exception as e:
            logging.error(f"Error in prediction: {e}")


def get_last_predicted_price():
    logging.info(f"Last predicted price: {last_predicted_price}")
    return last_predicted_price


def get_last_candle_data():
    logging.info(f"Last candle data: {last_candle_data}")
    return last_candle_data  # Returns the last candle information


def get_prediction_statistics():
    logging.info(f"Prediction statistics - Successful: {successful_predictions}, Unsuccessful: {unsuccessful_predictions}")
    return successful_predictions, unsuccessful_predictions


symbol = config.get("symbol", "BTCUSDT")
interval = config.get("interval", "5")
subscription_string = f"kline.{interval}.{symbol}"
socket_thread = threading.Thread(
    target=SocketConn,
    args=("wss://stream.bybit.com/v5/public/linear", [subscription_string]),
)
socket_thread.start()
