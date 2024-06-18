import logging
from datetime import datetime

from pmdarima import auto_arima
from pmdarima.arima import ARIMA
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import websocketBybit
from config import Config
from tradingview import get_technical_analysis
from logging_config import setup_logging

# Load configuration
config = Config()
token = config.get("telegram_bot_token")

# Set up logging
setup_logging("app.log")

# Function for /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    logging.info("Received /start command")
    if message:
        await message.reply_text("Привет! Я готов отправлять прогнозы цен.")
    logging.info("Sent start response")

# Function for /predict command
async def send_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    logging.info("Received /predict command")
    if message:
        predicted_price_gru, predicted_price_arima = websocketBybit.get_last_predicted_price()
        last_closing_prices = websocketBybit.last_closing_prices
        if predicted_price_gru is not None and predicted_price_arima is not None and last_closing_prices:
            current_price = last_closing_prices[-1]

            difference_gru = predicted_price_gru - current_price
            difference_percentage_gru = (difference_gru / current_price) * 100
            prediction_gru = "вырастет 📈" if difference_gru > 0 else "упадет 📉"
            
            difference_arima = predicted_price_arima - current_price
            difference_percentage_arima = (difference_arima / current_price) * 100
            prediction_arima = "вырастет 📈" if difference_arima > 0 else "упадет 📉"

            response = f"""
                GRU:
                Прогнозируемая следующая цена закрытия: {predicted_price_gru}
                Текущая цена: {current_price}
                Разница: {difference_gru}
                Разница в процентах: {difference_percentage_gru:.2f}%
                Прогноз: Цена {prediction_gru}
                
                ARIMA:
                Прогнозируемая следующая цена закрытия: {predicted_price_arima}
                Текущая цена: {current_price}
                Разница: {difference_arima}
                Разница в процентах: {difference_percentage_arima:.2f}%
                Прогноз: Цена {prediction_arima}
            """
            await message.reply_text(response)
            logging.info("Sent prediction response")
        else:
            await message.reply_text("Прогноз еще недоступен. Подождите немного.")
            logging.info("Prediction not available")

# Function for /current command
async def send_current_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    logging.info("Received /current command")
    if message:
        candle_data = websocketBybit.get_last_candle_data()
        if candle_data:
            start_timestamp = candle_data["start"]
            end_timestamp = candle_data["end"]
            start_str = datetime.fromtimestamp(start_timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
            end_str = datetime.fromtimestamp(end_timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
            response = f"""
                Interval: {candle_data['interval']} min
                Start: {start_str}, End: {end_str}
                Open: {candle_data['open']}, Close: {candle_data['close']}
                High: {candle_data['high']}, Low: {candle_data['low']}
                Volume: {candle_data['volume']}, Turnover: {candle_data['turnover']}
            """
            await message.reply_text(response)
            logging.info("Sent current candle data response")
        else:
            await message.reply_text("Актуальная информация еще недоступна. Подождите немного.")
            logging.info("Current candle data not available")

# Function for /stats command
async def send_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    logging.info("Received /stats command")
    if message:
        successful_gru, unsuccessful_gru, successful_arima, unsuccessful_arima = websocketBybit.get_prediction_statistics()
        response = f"""
            Статистика прогнозов:

            GRU:
            Удачных прогнозов: {successful_gru}
            Неудачных прогнозов: {unsuccessful_gru}
            
            ARIMA:
            Удачных прогнозов: {successful_arima}
            Неудачных прогнозов: {unsuccessful_arima}
        """
        await message.reply_text(response)
        logging.info("Sent stats response")

# Function for /recommend command
async def send_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    logging.info("Received /recommend command")
    if message:
        args = context.args if context.args else []

        symbol = args[0] if len(args) > 0 else "BTCUSDT"
        interval = args[1] if len(args) > 1 else "5"
        screener = args[2] if len(args) > 2 else "crypto"
        exchange = args[3] if len(args) > 3 else "Bybit"

        try:
            analysis = get_technical_analysis(symbol, interval, screener, exchange)
            summary = analysis.summary

            response = f"""
                Рекомендация для {symbol} на {interval} интервале:
                Покупать: {summary['BUY']}
                Продавать: {summary['SELL']}
                Держать: {summary['NEUTRAL']}
                Итог: {summary['RECOMMENDATION']}
            """
            await message.reply_text(response)
            logging.info("Sent recommendation response")
        except Exception as e:
            await message.reply_text(f"Ошибка при получении данных: {e}")
            logging.error(f"Error getting recommendation: {e}")

# Create an Application instance
app = Application.builder().token(token).build()

# Register command handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("predict", send_prediction))
app.add_handler(CommandHandler("current", send_current_info))
app.add_handler(CommandHandler("stats", send_stats))
app.add_handler(CommandHandler("recommend", send_recommendation))

# Start polling
logging.info("Starting bot polling")
app.run_polling()
logging.info("Bot polling started")
