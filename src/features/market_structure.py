import pandas as pd


def add_market_structure(df: pd.DataFrame, lookback: int = 3) -> pd.DataFrame:

    df = df.copy()

    df["swing_high"] = (
        (df["high"] > df["high"].shift(1)) &
        (df["high"] > df["high"].shift(2)) &
        (df["high"] > df["high"].shift(3)) &
        (df["high"] > df["high"].shift(-1)) &
        (df["high"] > df["high"].shift(-2)) &
        (df["high"] > df["high"].shift(-3))
    )

    df["swing_low"] = (
        (df["low"] < df["low"].shift(1)) &
        (df["low"] < df["low"].shift(2)) &
        (df["low"] < df["low"].shift(3)) &
        (df["low"] < df["low"].shift(-1)) &
        (df["low"] < df["low"].shift(-2)) &
        (df["low"] < df["low"].shift(-3))
    )

    df["higher_high"] = False
    df["lower_high"] = False
    df["higher_low"] = False
    df["lower_low"] = False

    previous_high = None

    for idx in df.index[df["swing_high"]]:

        current_high = df.loc[idx, "high"]

        if previous_high is not None:

            if current_high > previous_high:
                df.loc[idx, "higher_high"] = True
            else:
                df.loc[idx, "lower_high"] = True

        previous_high = current_high
    
    previous_low = None

    for idx in df.index[df["swing_low"]]:

        current_low = df.loc[idx, "low"]

        if previous_low is not None:

            if current_low > previous_low:
                df.loc[idx, "higher_low"] = True
            else:
                df.loc[idx, "lower_low"] = True

        previous_low = current_low


    return df