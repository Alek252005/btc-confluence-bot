import pandas as pd

from src.data.binance_data import download_binance_klines


def get_h4_trend(
    start_date: str,
    end_date: str,
    symbol: str = "BTCUSDT",
) -> pd.DataFrame:
    """
    Calcola il trend higher timeframe usando dati Binance 1h.

    Nota importante:
    La funzione si chiama ancora get_h4_trend per non cambiare il resto del bot,
    ma la baseline attuale usava dati 1h da Yahoo, quindi manteniamo 1h.
    """

    h4 = download_binance_klines(
        symbol=symbol,
        interval="1h",
        start_date=start_date,
        end_date=end_date,
    )

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