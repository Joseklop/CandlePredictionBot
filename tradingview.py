from tradingview_ta import Interval, TA_Handler

# Mapping of interval strings to TradingView TA intervals
interval_map = {
    "1": Interval.INTERVAL_1_MINUTE,
    "5": Interval.INTERVAL_5_MINUTES,
    "15": Interval.INTERVAL_15_MINUTES,
    "30": Interval.INTERVAL_30_MINUTES,
    "60": Interval.INTERVAL_1_HOUR,
    "120": Interval.INTERVAL_2_HOURS,
    "240": Interval.INTERVAL_4_HOURS,
    "D": Interval.INTERVAL_1_DAY,
    "W": Interval.INTERVAL_1_WEEK,
    "M": Interval.INTERVAL_1_MONTH,
}


def get_technical_analysis(symbol="BTCUSDT", interval="D", screener="crypto", exchange="Bybit"):
    """
    Retrieve technical analysis for a given symbol, interval, screener, and exchange.

    Args:
        symbol (str): The trading pair symbol (default is "BTCUSDT").
        interval (str): The time interval for the analysis (default is "D").
        screener (str): The screener type (default is "crypto").
        exchange (str): The exchange name (default is "Bybit").

    Returns:
        Analysis: An analysis object containing the technical analysis data.

    Raises:
        ValueError: If the provided interval is not valid.
    """

    # Validate the interval
    if interval not in interval_map:
        raise ValueError(
            "Invalid interval. Allowed values: 1, 5, 15, 30, 60, 120, 240, D, W, M."
        )

    # Create a TA_Handler instance with the provided parameters
    handler = TA_Handler(
        symbol=symbol,
        screener=screener,
        exchange=exchange,
        interval=interval_map[interval],
    )

    # Get and return the analysis
    try:
        analysis = handler.get_analysis()
        return analysis
    except Exception as e:
        raise RuntimeError(f"Error retrieving technical analysis: {e}")


# Example usage
if __name__ == "__main__":
    try:
        analysis = get_technical_analysis(symbol="BTCUSDT", interval="D")
        print(analysis.summary)
    except Exception as e:
        print(f"Failed to get technical analysis: {e}")
