import pandas as pd
import yfinance as yf


def get_h4_trend():

    h4 = yf.download(
        "BTC-USD",
        period="60d",
        interval="1h",
        auto_adjust=True,
        progress=False
    )

    if isinstance(h4.columns, pd.MultiIndex):
        h4.columns = h4.columns.get_level_values(0)

    h4 = h4.rename(columns=str.lower)

    h4["ema_50"] = h4["close"].ewm(span=50).mean()
    h4["ema_200"] = h4["close"].ewm(span=200).mean()

    h4["h4_uptrend"] = (
        (h4["close"] > h4["ema_50"]) &
        (h4["ema_50"] > h4["ema_200"])
    )

    h4["h4_downtrend"] = (
        (h4["close"] < h4["ema_50"]) &
        (h4["ema_50"] < h4["ema_200"])
    )

    return h4[[
        "h4_uptrend",
        "h4_downtrend"
    ]]