import os
import json
import websocket
import threading
import _thread
import keyboard
from datetime import datetime
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import numpy as np

from config import Config

# Загрузка конфигурации
config = Config()

# Загрузка модели GRU
model = load_model(config.model_path)
scaler = MinMaxScaler(feature_range=(0, 1))

# Создание списка для отслеживания последних значений свечей
last_closing_prices = []
last_predicted_price = None
last_candle_data = None

# Статистика
successful_predictions = 0
unsuccessful_predictions = 0

class SocketConn(websocket.WebSocketApp):
    def __init__(self, url, params=[]):
        super().__init__(url=url, on_open=self.on_open)
        self.params = params
        self.on_message = lambda ws, msg: self.message(msg)
        self.on_error = lambda ws, e: print('Error', e)
        self.on_close = lambda ws: print('Closing')
        self.last_kline_timestamp = None
        self.thread = threading.Thread(target=self.run_forever)
        self.thread.start()

    def on_open(self, ws):
        print('WebSocket был открыт')

        def run(*args):
            trade_str = {"op": "subscribe", "args": self.params}
            ws.send(json.dumps(trade_str))
        _thread.start_new_thread(run, ())

    def message(self, msg):
        global last_candle_data, successful_predictions, unsuccessful_predictions
        data = json.loads(msg)
        if 'topic' in data and data['topic'].startswith('kline'):
            kline_info = data['data'][0]
            close_price = float(kline_info['close'])
            end_timestamp = kline_info['end']

            last_candle_data = kline_info  # Сохраняем последние данные свечий

            if self.last_kline_timestamp != end_timestamp:
                self.last_kline_timestamp = end_timestamp

                if len(last_closing_prices) >= config.get('window_size', 40):
                    last_closing_prices.pop(0) 
                last_closing_prices.append(close_price)

                if len(last_closing_prices) == config.get('window_size', 40):
                    self.predict_next_candle()

                start_timestamp = kline_info['start']
                start_str = datetime.utcfromtimestamp(start_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
                end_str = datetime.utcfromtimestamp(end_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
                print(f"""Криптовалюта: {symbol}, Интервал: {kline_info['interval']} min
                Данные свечи:
                Start: {start_str}, End: {end_str}
                Open: {kline_info['open']}, Close: {close_price}
                High: {kline_info['high']}, Low: {kline_info['low']}
                Volume: {kline_info['volume']}, Turnover: {kline_info['turnover']}
                """)

    def predict_next_candle(self):
        global last_predicted_price, successful_predictions, unsuccessful_predictions
        last_prices = np.array(last_closing_prices).reshape(-1, 1)
        scaled_data = scaler.fit_transform(last_prices)
        X_test = np.reshape(scaled_data, (1, scaled_data.shape[0], 1))
        if X_test.shape[1] == config.get('window_size', 40):
            predicted_price = model.predict(X_test) 
            last_predicted_price = scaler.inverse_transform(predicted_price)[0][0]
            print(f'Прогнозируемая цена: {last_predicted_price}')

            if last_predicted_price and last_closing_prices:
                current_price = last_closing_prices[-1]
                difference = last_predicted_price - current_price
                difference_percentage = (difference / current_price) * 100
                prediction = "вырастет 📈" if difference > 0 else "упадет 📉"
                print(f"Текущая цена: {current_price}, Прогнозируемая цена: {last_predicted_price}")
                print(f"Разница: {difference}, Разница в процентах: {difference_percentage:.2f}%, Прогноз: Цена {prediction}")

                # Обновление статистики
                if (difference > 0 and current_price > last_closing_prices[-2]) or (difference < 0 and current_price < last_closing_prices[-2]):
                    successful_predictions += 1
                else:
                    unsuccessful_predictions += 1

def get_last_predicted_price():
    return last_predicted_price

def get_last_candle_data():
    return last_candle_data  # Функция возвращает последнюю информацию о свече

def get_prediction_statistics():
    return successful_predictions, unsuccessful_predictions

def exit_on_keypress():
    print("Press 'q' to exit.")
    while True:
        if keyboard.is_pressed('q'):
            print("Exiting program...")
            os._exit(0)

symbol = config.get('symbol', 'BTCUSDT')
interval = config.get('interval', '5')
subscription_string = f"kline.{interval}.{symbol}"
socket_thread = threading.Thread(target=SocketConn, args=('wss://stream.bybit.com/v5/public/linear', [subscription_string]))
socket_thread.start()

exit_thread = threading.Thread(target=exit_on_keypress)
exit_thread.start()
