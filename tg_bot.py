from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import json
import os

import websocketBybit
from config import Config
from datetime import datetime
from tradingview import get_technical_analysis

# Загрузка конфигурации
config = Config()
token = config.get('telegram_bot_token')

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Функция для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Я готов отправлять прогнозы цен.')

# Функция для команды /predict
async def send_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    predicted_price = websocketBybit.get_last_predicted_price()
    if predicted_price is not None:
        await update.message.reply_text(f"""
        Прогнозируемая следующая цена закрытия: {predicted_price}
        """)
    else:
        await update.message.reply_text('Прогноз еще недоступен. Подождите немного.')

# Функция для команды /current
async def send_current_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    candle_data = websocketBybit.get_last_candle_data()
    if candle_data is not None:
        start_timestamp = candle_data['start']
        end_timestamp = candle_data['end']
        start_str = datetime.utcfromtimestamp(start_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        end_str = datetime.utcfromtimestamp(end_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        await update.message.reply_text(f"""
        Interval: {candle_data['interval']} min
        Start: {start_str}, End: {end_str}
        Open: {candle_data['open']}, Close: {candle_data['close']}
        High: {candle_data['high']}, Low: {candle_data['low']}
        Volume: {candle_data['volume']}, Turnover: {candle_data['turnover']}
        """)
    else:
        await update.message.reply_text('Актуальная информация еще недоступна. Подождите немного.')

# Функция для команды /stats
async def send_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    successful, unsuccessful = websocketBybit.get_prediction_statistics()
    await update.message.reply_text(f"""
    Статистика прогнозов:
    Удачных прогнозов: {successful}
    Неудачных прогнозов: {unsuccessful}
    """)

# Функция для команды /recommend
async def send_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        args = context.args

        symbol = args[0] if len(args) > 0 else 'BTCUSDT'
        interval = args[1] if len(args) > 1 else '5'
        screener = args[2] if len(args) > 2 else 'crypto'
        exchange = args[3] if len(args) > 3 else 'Bybit'

    try:
        analysis = get_technical_analysis(symbol, interval, screener, exchange)
        summary = analysis.summary

        await update.message.reply_text(f"""
        Рекомендация для {symbol} на {interval} интервале:
        Покупать: {summary['BUY']}
        Продавать: {summary['SELL']}
        Держать: {summary['NEUTRAL']}
        Итог: {summary['RECOMMENDATION']}
        """)
    except Exception as e:
        await update.message.reply_text(f'Ошибка при получении данных: {e}')


# Создание экземпляра Application
app = Application.builder().token(token).build()

# Регистрация обработчиков команд
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('predict', send_prediction))
app.add_handler(CommandHandler('current', send_current_info)) 
app.add_handler(CommandHandler('stats', send_stats))
app.add_handler(CommandHandler('recommend', send_recommendation))

# Начало опроса
app.run_polling()