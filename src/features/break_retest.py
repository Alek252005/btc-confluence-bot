import pandas as pd


def add_break_retest(
    df: pd.DataFrame,
    lookback: int = 50,
    retest_tolerance_atr: float = 0.25,
    max_retest_bars: int = 10
) -> pd.DataFrame:

    df = df.copy()

    df["break_retest_level_long"] = pd.NA
    df["break_retest_level_short"] = pd.NA

    df["bullish_break"] = False
    df["bearish_break"] = False
    df["bullish_break_retest"] = False
    df["bearish_break_retest"] = False

    df["last_swing_high"] = df["high"].where(df["swing_high"]).ffill().shift(1)
    df["last_swing_low"] = df["low"].where(df["swing_low"]).ffill().shift(1)

    for i in range(lookback, len(df)):
        current_close = df.iloc[i]["close"]
        previous_close = df.iloc[i - 1]["close"]

        swing_high_level = df.iloc[i]["last_swing_high"]
        swing_low_level = df.iloc[i]["last_swing_low"]

        if pd.notna(swing_high_level):
            bullish_break = (
                previous_close <= swing_high_level and
                current_close > swing_high_level
            )

            if bullish_break:
                df.iloc[i, df.columns.get_loc("bullish_break")] = True

                for j in range(i + 1, min(i + 1 + max_retest_bars, len(df))):
                    atr = df.iloc[j]["atr_14"]
                    tolerance = atr * retest_tolerance_atr

                    retest = df.iloc[j]["low"] <= swing_high_level + tolerance
                    holds_level = df.iloc[j]["close"] > swing_high_level

                    confirmation = (
                        df.iloc[j]["bullish_engulfing"] or
                        df.iloc[j]["bullish_382_candle"] 
                    )

                    if retest and holds_level and confirmation:
                        df.iloc[j, df.columns.get_loc("bullish_break_retest")] = True
                        df.iloc[j, df.columns.get_loc("break_retest_level_long")] = swing_high_level
                        break

        if pd.notna(swing_low_level):
            bearish_break = (
                previous_close >= swing_low_level and
                current_close < swing_low_level
            )

            if bearish_break:
                df.iloc[i, df.columns.get_loc("bearish_break")] = True

                for j in range(i + 1, min(i + 1 + max_retest_bars, len(df))):
                    atr = df.iloc[j]["atr_14"]
                    tolerance = atr * retest_tolerance_atr

                    retest = df.iloc[j]["high"] >= swing_low_level - tolerance
                    holds_level = df.iloc[j]["close"] < swing_low_level

                    confirmation = (
                        df.iloc[j]["bearish_engulfing"] or
                        df.iloc[j]["bearish_382_candle"] 
                    )

                    if retest and holds_level and confirmation:
                        df.iloc[j, df.columns.get_loc("bearish_break_retest")] = True
                        df.iloc[j, df.columns.get_loc("break_retest_level_short")] = swing_low_level
                        break

    return df