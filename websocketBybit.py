import _thread
import json
import logging
import os
import threading
from datetime import datetime

import numpy as np
from pmdarima import auto_arima
from pmdarima.arima import ARIMA
import websocket
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model

from config import Config
from logging_config import setup_logging

# Set environment variable to turn off oneDNN optimizations
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

setup_logging("app.log")

# Load configuration
config = Config()

# Load the GRU model
model = load_model(config.model_path)
scaler = MinMaxScaler(feature_range=(0, 1))

# Initialize variables
last_closing_prices = []
last_predicted_price_gru = None
last_predicted_price_arima = None
last_candle_data = None

successful_predictions_gru = 71
unsuccessful_predictions_gru = 236

successful_predictions_arima = 20
unsuccessful_predictions_arima = 112

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
        global last_candle_data, successful_predictions_gru, unsuccessful_predictions_gru

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
        global last_predicted_price_gru, last_predicted_price_arima
        global successful_predictions_gru, unsuccessful_predictions_gru
        global successful_predictions_arima, unsuccessful_predictions_arima
        try:
            # GRU Prediction
            last_prices = np.array(last_closing_prices).reshape(-1, 1)
            scaled_data = scaler.fit_transform(last_prices)
            X_test = np.reshape(scaled_data, (1, scaled_data.shape[0], 1))
            predicted_price_gru = model.predict(X_test)
            last_predicted_price_gru = scaler.inverse_transform(predicted_price_gru)[0][0]
            logging.info(f"Прогнозируемая цена (GRU): {last_predicted_price_gru}")

            # ARIMA Prediction
            history = list(last_closing_prices)
            model_arima = auto_arima(history, start_p=1, start_q=1, max_p=3, max_q=3, d=1,
                                     trace=False, error_action='ignore', suppress_warnings=True)
            forecast_arima = model_arima.predict(n_periods=1)[0]
            last_predicted_price_arima = forecast_arima
            logging.info(f"Прогнозируемая цена (ARIMA): {last_predicted_price_arima}")


            if last_predicted_price_gru and last_closing_prices:
                current_price = last_closing_prices[-1]
                previous_price = last_closing_prices[-2]

                # GRU Evaluation
                difference_gru = last_predicted_price_gru - current_price
                difference_percentage_gru = (difference_gru / current_price) * 100
                prediction_gru = "вырастет 📈" if difference_gru > 0 else "упадет 📉"
                logging.info(
                    f"GRU - Текущая цена: {current_price}, Прогнозируемая цена: {last_predicted_price_gru}"
                )
                logging.info(
                    f"GRU - Разница: {difference_gru}, Разница в процентах: {difference_percentage_gru:.2f}%, Прогноз: Цена {prediction_gru}"
                )

                # ARIMA Evaluation
                difference_arima = last_predicted_price_arima - current_price
                difference_percentage_arima = (difference_arima / current_price) * 100
                prediction_arima = "вырастет 📈" if difference_arima > 0 else "упадет 📉"
                logging.info(
                    f"ARIMA - Текущая цена: {current_price}, Прогнозируемая цена: {last_predicted_price_arima}"
                )
                logging.info(
                    f"ARIMA - Разница: {difference_arima}, Разница в процентах: {difference_percentage_arima:.2f}%, Прогноз: Цена {prediction_arima}"
                )

                # Update statistics for GRU
                if (difference_gru > 0 and current_price > previous_price) or (
                    difference_gru < 0 and current_price < previous_price
                ):
                    successful_predictions_gru += 1
                else:
                    unsuccessful_predictions_gru += 1

                # Update statistics for ARIMA
                if (difference_arima > 0 and current_price > previous_price) or (
                    difference_arima < 0 and current_price < previous_price
                ):
                    successful_predictions_arima += 1
                else:
                    unsuccessful_predictions_arima += 1

                logging.info(
                    f"Updated statistics - GRU Successful: {successful_predictions_gru}, Unsuccessful: {unsuccessful_predictions_gru}"
                )
                logging.info(
                    f"Updated statistics - ARIMA Successful: {successful_predictions_arima}, Unsuccessful: {unsuccessful_predictions_arima}"
                )
        except Exception as e:
            logging.error(f"Error in prediction: {e}")


def get_last_predicted_price():
    logging.info(f"Last predicted price (GRU): {last_predicted_price_gru}")
    logging.info(f"Last predicted price (ARIMA): {last_predicted_price_arima}")
    return last_predicted_price_gru, last_predicted_price_arima

def get_last_candle_data():
    logging.info(f"Last candle data: {last_candle_data}")
    return last_candle_data  # Returns the last candle information


def get_prediction_statistics():
    logging.info(
            f"""Prediction statistics GRU:
                    Successful: {successful_predictions_gru}, 
                    Unsuccessful: {unsuccessful_predictions_gru}
                    Prediction statistics ARIMA:
                    Successful: {successful_predictions_arima}, 
                    Unsuccessful: {unsuccessful_predictions_arima}"""
            )
    return successful_predictions_gru, unsuccessful_predictions_gru, successful_predictions_arima, unsuccessful_predictions_arima


symbol = config.get("symbol", "BTCUSDT")
interval = config.get("interval", "5")
subscription_string = f"kline.{interval}.{symbol}"
socket_thread = threading.Thread(
    target=SocketConn,
    args=("wss://stream.bybit.com/v5/public/linear", [subscription_string]),
)
socket_thread.start()
