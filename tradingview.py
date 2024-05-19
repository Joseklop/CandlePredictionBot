from tradingview_ta import TA_Handler, Interval

interval_map = {
    '1': Interval.INTERVAL_1_MINUTE,
    '5': Interval.INTERVAL_5_MINUTES,
    '15': Interval.INTERVAL_15_MINUTES,
    '30': Interval.INTERVAL_30_MINUTES,
    '60': Interval.INTERVAL_1_HOUR,
    '120': Interval.INTERVAL_2_HOURS,
    '240': Interval.INTERVAL_4_HOURS,
    'D': Interval.INTERVAL_1_DAY,
    'W': Interval.INTERVAL_1_WEEK,
    'M': Interval.INTERVAL_1_MONTH,
}

def get_technical_analysis(symbol="BTCUSDT", interval="D", screener="crypto", exchange="Bybit"):
    if interval not in interval_map:
        raise ValueError("Invalid interval. Allowed values: 1, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M.")
    
    handler = TA_Handler(
        symbol=symbol,
        screener=screener,
        exchange=exchange,
        interval=interval_map[interval]
    )

    analysis = handler.get_analysis()
    return analysis