import pandas as pd


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggiunge al dataframe gli indicatori base:
    - EMA20
    - EMA50
    - EMA200
    - ATR14
    """

    df = df.copy()

    df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()

    df["prev_close"] = df["close"].shift(1)

    df["tr_1"] = df["high"] - df["low"]
    df["tr_2"] = (df["high"] - df["prev_close"]).abs()
    df["tr_3"] = (df["low"] - df["prev_close"]).abs()

    df["true_range"] = df[["tr_1", "tr_2", "tr_3"]].max(axis=1)
    df["atr_14"] = df["true_range"].ewm(span=14, adjust=False).mean()

    return df