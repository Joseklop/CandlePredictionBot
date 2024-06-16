import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import websocketBybit
from config import Config
from tradingview import get_technical_analysis

# Load configuration
config = Config()
token = config.get("telegram_bot_token")

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# Function for /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message:
        await message.reply_text("Привет! Я готов отправлять прогнозы цен.")


# Function for /predict command
async def send_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message:
        predicted_price = websocketBybit.get_last_predicted_price()
        last_closing_prices = websocketBybit.last_closing_prices
        if predicted_price is not None and last_closing_prices:
            current_price = last_closing_prices[-1]
            difference = predicted_price - current_price
            difference_percentage = (difference / current_price) * 100
            prediction = "вырастет 📈" if difference > 0 else "упадет 📉"

            await message.reply_text(
                f"""
                Прогнозируемая следующая цена закрытия: {predicted_price}
                Текущая цена: {current_price}
                Разница: {difference}
                Разница в процентах: {difference_percentage:.2f}%
                Прогноз: Цена {prediction}
                """
            )
        else:
            await message.reply_text("Прогноз еще недоступен. Подождите немного.")


# Function for /current command
async def send_current_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message:
        candle_data = websocketBybit.get_last_candle_data()
        if candle_data:
            start_timestamp = candle_data["start"]
            end_timestamp = candle_data["end"]
            start_str = datetime.fromtimestamp(start_timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
            end_str = datetime.fromtimestamp(end_timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
            await message.reply_text(
                f"""
                Interval: {candle_data['interval']} min
                Start: {start_str}, End: {end_str}
                Open: {candle_data['open']}, Close: {candle_data['close']}
                High: {candle_data['high']}, Low: {candle_data['low']}
                Volume: {candle_data['volume']}, Turnover: {candle_data['turnover']}
                """
            )
        else:
            await message.reply_text("Актуальная информация еще недоступна. Подождите немного.")


# Function for /stats command
async def send_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message:
        successful, unsuccessful = websocketBybit.get_prediction_statistics()
        await message.reply_text(
            f"""
            Статистика прогнозов:
            Удачных прогнозов: {successful}
            Неудачных прогнозов: {unsuccessful}
            """
        )


# Function for /recommend command
async def send_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message:
        args = context.args if context.args else []

        symbol = args[0] if len(args) > 0 else "BTCUSDT"
        interval = args[1] if len(args) > 1 else "5"
        screener = args[2] if len(args) > 2 else "crypto"
        exchange = args[3] if len(args) > 3 else "Bybit"

        try:
            analysis = get_technical_analysis(symbol, interval, screener, exchange)
            summary = analysis.summary

            await message.reply_text(
                f"""
                Рекомендация для {symbol} на {interval} интервале:
                Покупать: {summary['BUY']}
                Продавать: {summary['SELL']}
                Держать: {summary['NEUTRAL']}
                Итог: {summary['RECOMMENDATION']}
                """
            )
        except Exception as e:
            await message.reply_text(f"Ошибка при получении данных: {e}")

# Create an Application instance
app = Application.builder().token(token).build()

# Register command handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("predict", send_prediction))
app.add_handler(CommandHandler("current", send_current_info))
app.add_handler(CommandHandler("stats", send_stats))
app.add_handler(CommandHandler("recommend", send_recommendation))

# Start polling
app.run_polling()
