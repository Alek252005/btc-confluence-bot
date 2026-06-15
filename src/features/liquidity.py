import pandas as pd


def add_equal_highs_lows(
    df: pd.DataFrame,
    lookback: int = 50,
    tolerance_atr: float = 0.25
) -> pd.DataFrame:

    df = df.copy()

    df["equal_high"] = False
    df["equal_low"] = False

    for i in range(lookback, len(df)):
        current_high = df.iloc[i]["high"]
        current_low = df.iloc[i]["low"]
        atr = df.iloc[i]["atr_14"]

        tolerance = atr * tolerance_atr

        recent_highs = df.iloc[i - lookback:i]
        recent_lows = df.iloc[i - lookback:i]

        previous_similar_highs = recent_highs[
            (recent_highs["swing_high"]) &
            ((recent_highs["high"] - current_high).abs() <= tolerance)
        ]

        previous_similar_lows = recent_lows[
            (recent_lows["swing_low"]) &
            ((recent_lows["low"] - current_low).abs() <= tolerance)
        ]

        if len(previous_similar_highs) > 0:
            df.iloc[i, df.columns.get_loc("equal_high")] = True

        if len(previous_similar_lows) > 0:
            df.iloc[i, df.columns.get_loc("equal_low")] = True

    return df

def add_liquidity_sweeps(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    df["bullish_sweep"] = (
        df["equal_low"] &
        (df["low"] < df["low"].shift(1)) &
        (df["close"] > df["open"])
    )

    df["bearish_sweep"] = (
        df["equal_high"] &
        (df["high"] > df["high"].shift(1)) &
        (df["close"] < df["open"])
    )

    return df