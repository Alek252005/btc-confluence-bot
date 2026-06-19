import pandas as pd


def generate_playbook_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strategia alternativa "trader playbook".

    Non entra perché un punteggio supera una soglia.
    Entra solo se passano 4 blocchi:
    1. contesto trend
    2. bias direzionale
    3. zona di pullback
    4. trigger candlestick / liquidity / break retest
    """

    df = df.copy()

    df["bullish_candle"] = df["close"] > df["open"]
    df["bearish_candle"] = df["close"] < df["open"]

    # Struttura recente
    recent_bullish_structure = (
        df["higher_high"].rolling(20).max().fillna(False).astype(bool) |
        df["higher_low"].rolling(20).max().fillna(False).astype(bool)
    )

    recent_bearish_structure = (
        df["lower_high"].rolling(20).max().fillna(False).astype(bool) |
        df["lower_low"].rolling(20).max().fillna(False).astype(bool)
    )

    # Engulfing forte
    df["body_size"] = (df["close"] - df["open"]).abs()
    df["avg_body_10"] = df["body_size"].rolling(10).mean()

    df["bullish_engulfing_strong"] = (
        df["bullish_engulfing"] &
        (df["body_size"] > df["avg_body_10"] * 1.2)
    )

    df["bearish_engulfing_strong"] = (
        df["bearish_engulfing"] &
        (df["body_size"] > df["avg_body_10"] * 1.2)
    )

    # Forza trend: EMA ordinate + pendenza EMA50
    ema50_slope_12 = df["ema_50"] - df["ema_50"].shift(12)

    long_trend_context = (
        df["h4_uptrend"] &
        (df["ema_20"] > df["ema_50"]) &
        (df["ema_50"] > df["ema_200"]) &
        (df["close"] > df["ema_200"]) &
        (ema50_slope_12 > 0) &
        recent_bullish_structure
    )

    short_trend_context = (
        df["h4_downtrend"] &
        (df["ema_20"] < df["ema_50"]) &
        (df["ema_50"] < df["ema_200"]) &
        (df["close"] < df["ema_200"]) &
        (ema50_slope_12 < 0) &
        recent_bearish_structure
    )

    # Evita mercato troppo piatto: EMA20 e EMA50 devono essere abbastanza separate
    trend_not_flat = (
        (df["ema_20"] - df["ema_50"]).abs() >
        (df["atr_14"] * 0.15)
    )

    long_context_ok = long_trend_context & trend_not_flat
    short_context_ok = short_trend_context & trend_not_flat

    # Zona: pullback verso EMA20/EMA50, non entrata a caso
    long_zone = (
        (
            (df["low"] <= df["ema_20"]) |
            (df["low"] <= df["ema_50"])
        ) &
        (df["close"] > df["ema_20"])
    )

    short_zone = (
        (
            (df["high"] >= df["ema_20"]) |
            (df["high"] >= df["ema_50"])
        ) &
        (df["close"] < df["ema_20"])
    )

    # Evita di entrare troppo lontano dalla EMA20
    long_not_chasing = (
        (df["close"] - df["ema_20"]).abs() <=
        (df["atr_14"] * 2.0)
    )

    short_not_chasing = (
        (df["close"] - df["ema_20"]).abs() <=
        (df["atr_14"] * 2.0)
    )

    # Trigger: candela/conferma vera
    long_trigger = (
        df["bullish_engulfing_strong"] |
        df["bullish_382_candle"] |
        df["bullish_break_retest"] |
        (
            df["bullish_sweep"] &
            df["bullish_candle"]
        )
    )

    short_trigger = (
        df["bearish_engulfing_strong"] |
        df["bearish_382_candle"] |
        df["bearish_break_retest"] |
        (
            df["bearish_sweep"] &
            df["bearish_candle"]
        )
    )

    df["long_signal"] = (
        long_context_ok &
        long_zone &
        long_not_chasing &
        long_trigger
    )

    df["short_signal"] = (
        short_context_ok &
        short_zone &
        short_not_chasing &
        short_trigger
    )

    # Score solo per compatibilità con il backtest/report.
    # Non viene usato per decidere l'ingresso.
    df["long_score"] = 0
    df["short_score"] = 0

    df.loc[long_context_ok, "long_score"] += 40
    df.loc[long_zone, "long_score"] += 30
    df.loc[long_trigger, "long_score"] += 30

    df.loc[short_context_ok, "short_score"] += 40
    df.loc[short_zone, "short_score"] += 30
    df.loc[short_trigger, "short_score"] += 30

    return df