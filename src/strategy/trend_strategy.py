import pandas as pd


def generate_signals(df: pd.DataFrame, trend_mode: str = "hybrid") -> pd.DataFrame:
    """
    Genera segnali LONG e SHORT con più confluenze:
    - trend EMA20/EMA50/EMA200
    - pullback su EMA20
    - candela di conferma
    - score minimo
    """

    df = df.copy()

    df["bullish_candle"] = df["close"] > df["open"]
    df["bearish_candle"] = df["close"] < df["open"]

    recent_bullish_structure = (
        df["higher_high"].rolling(20).max().astype(bool) |
        df["higher_low"].rolling(20).max().astype(bool)
    )

    recent_bearish_structure = (
        df["lower_high"].rolling(20).max().astype(bool) |
        df["lower_low"].rolling(20).max().astype(bool)
    )

    ema_uptrend = (
        (df["ema_20"] > df["ema_50"]) &
        (df["ema_50"] > df["ema_200"]) &
        (df["close"] > df["ema_20"]) &
        (df["close"] > df["ema_200"]) &
        (df["close"] > df["close"].shift(20))
        
    )

    ema_downtrend = (
        (df["ema_20"] < df["ema_50"]) &
        (df["ema_50"] < df["ema_200"]) &
        (df["close"] < df["ema_20"]) &
        (df["close"] < df["ema_200"]) &
        (df["close"] < df["close"].shift(20))
    )

    if trend_mode == "hybrid":
        df["uptrend"] = ema_uptrend & recent_bullish_structure
        df["downtrend"] = ema_downtrend & recent_bearish_structure

    elif trend_mode == "structure":
        df["uptrend"] = recent_bullish_structure
        df["downtrend"] = recent_bearish_structure

    else:
        raise ValueError("trend_mode deve essere 'hybrid' oppure 'structure'")

    df["long_pullback"] = (
        (df["low"] <= df["ema_20"]) &
        (df["close"] > df["ema_20"])
    )

    df["short_pullback"] = (
        (df["high"] >= df["ema_20"]) &
        (df["close"] < df["ema_20"])
    )

    df["long_score"] = 0
    df["short_score"] = 0

    df.loc[df["uptrend"], "long_score"] += 40
    df.loc[df["long_pullback"], "long_score"] += 30
    df.loc[df["bullish_sweep"], "long_score"] += 15
    df.loc[df["bullish_break_retest"], "long_score"] += 20
    df.loc[df["bullish_engulfing"], "long_score"] += 20
    df.loc[df["atr_14"] > 0, "long_score"] += 10

    df.loc[df["downtrend"], "short_score"] += 40
    df.loc[df["short_pullback"], "short_score"] += 30
    df.loc[df["bearish_sweep"], "short_score"] += 15
    df.loc[df["bearish_break_retest"], "short_score"] += 20
    df.loc[df["bearish_engulfing"], "short_score"] += 20
    df.loc[df["atr_14"] > 0, "short_score"] += 10

    df["long_signal"] = (
        df["h4_uptrend"] &
        (df["long_score"] >= 80) &
        (
            df["bullish_engulfing"] |
            df["bullish_382_candle"] |
            df["bullish_break_retest"]
        )
    )

    df["short_signal"] = (
        df["h4_downtrend"] &
        (df["short_score"] >= 80) &
        (
            df["bearish_engulfing"] |
            df["bearish_382_candle"] |
            df["bearish_break_retest"]
        )   
    )

    return df