import logging
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import websocketBybit
from config import Config
from tradingview import get_technical_analysis

# Загрузка конфигурации
config = Config()
token = config.get("telegram_bot_token")

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# Функция для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("Привет! Я готов отправлять прогнозы цен.")


# Функция для команды /predict
async def send_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    predicted_price = websocketBybit.get_last_predicted_price()
    last_closing_prices = websocketBybit.last_closing_prices
    if predicted_price is not None and last_closing_prices:
        current_price = last_closing_prices[-1]
        difference = predicted_price - current_price
        difference_percentage = (difference / current_price) * 100
        prediction = "вырастет 📈" if difference > 0 else "упадет 📉"

        if update.message:
            await update.message.reply_text(
                f"""
            Прогнозируемая следующая цена закрытия: {predicted_price}
            Текущая цена: {current_price}
            Разница: {difference}
            Разница в процентах: {difference_percentage:.2f}%
            Прогноз: Цена {prediction}
            """
            )
    else:
        if update.message:
            await update.message.reply_text("Прогноз еще недоступен. Подождите немного.")


# Функция для команды /current
async def send_current_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    candle_data = websocketBybit.get_last_candle_data()
    if candle_data is not None:
        start_timestamp = candle_data["start"]
        end_timestamp = candle_data["end"]
        start_str = datetime.fromtimestamp(start_timestamp / 1000).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        end_str = datetime.fromtimestamp(end_timestamp / 1000).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if update.message:
            await update.message.reply_text(
                f"""
            Interval: {candle_data['interval']} min
            Start: {start_str}, End: {end_str}
            Open: {candle_data['open']}, Close: {candle_data['close']}
            High: {candle_data['high']}, Low: {candle_data['low']}
            Volume: {candle_data['volume']}, Turnover: {candle_data['turnover']}
            """
            )
    else:
        if update.message:
            await update.message.reply_text(
                "Актуальная информация еще недоступна. Подождите немного."
            )


# Функция для команды /stats
async def send_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    successful, unsuccessful = websocketBybit.get_prediction_statistics()
    if update.message:
        await update.message.reply_text(
            f"""
        Статистика прогнозов:
        Удачных прогнозов: {successful}
        Неудачных прогнозов: {unsuccessful}
        """
        )


# Функция для команды /recommend
async def send_recommendation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if update.message:
        args = context.args if context.args else []

        symbol = args[0] if len(args) > 0 else "BTCUSDT"
        interval = args[1] if len(args) > 1 else "5"
        screener = args[2] if len(args) > 2 else "crypto"
        exchange = args[3] if len(args) > 3 else "Bybit"

        try:
            analysis = get_technical_analysis(symbol, interval, screener, exchange)
            summary = analysis.summary

            await update.message.reply_text(
                f"""
            Рекомендация для {symbol} на {interval} интервале:
            Покупать: {summary['BUY']}
            Продавать: {summary['SELL']}
            Держать: {summary['NEUTRAL']}
            Итог: {summary['RECOMMENDATION']}
            """
            )
        except Exception as e:
            await update.message.reply_text(f"Ошибка при получении данных: {e}")


# Создание экземпляра Application
app = Application.builder().token(token).build()

# Регистрация обработчиков команд
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("predict", send_prediction))
app.add_handler(CommandHandler("current", send_current_info))
app.add_handler(CommandHandler("stats", send_stats))
app.add_handler(CommandHandler("recommend", send_recommendation))

# Начало опроса
app.run_polling()
