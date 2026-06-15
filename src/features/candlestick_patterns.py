import pandas as pd


def add_candlestick_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggiunge pattern candlestick:
    - bullish_engulfing
    - bearish_engulfing
    - bullish_382_candle
    - bearish_382_candle
    """

    df = df.copy()

    prev_open = df["open"].shift(1)
    prev_close = df["close"].shift(1)

    prev_bearish = prev_close < prev_open
    prev_bullish = prev_close > prev_open

    current_bullish = df["close"] > df["open"]
    current_bearish = df["close"] < df["open"]

    current_body = (df["close"] - df["open"]).abs()
    previous_body = (prev_close - prev_open).abs()

    df["bullish_engulfing"] = (
        prev_bearish &
        current_bullish &
        (current_body > previous_body)
    )

    df["bearish_engulfing"] = (
        prev_bullish &
        current_bearish &
        (current_body > previous_body)
    )

    candle_range = df["high"] - df["low"]

    bullish_382_level = df["low"] + (candle_range * 0.382)
    bearish_382_level = df["high"] - (candle_range * 0.382)

    df["bullish_382_candle"] = (
        current_bullish &
        (candle_range > 0) &
        (df["open"] > bullish_382_level) &
        (df["close"] > bullish_382_level)
    )

    df["bearish_382_candle"] = (
        current_bearish &
        (candle_range > 0) &
        (df["open"] < bearish_382_level) &
        (df["close"] < bearish_382_level)
    )

    return df