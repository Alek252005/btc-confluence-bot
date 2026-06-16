import json
import time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd


BINANCE_BASE_URL = "https://api.binance.com"


def _date_to_milliseconds(date_str: str) -> int:
    """
    Converte una data tipo '2024-01-01' in millisecondi UTC.
    """
    dt = datetime.fromisoformat(date_str)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return int(dt.timestamp() * 1000)


def _interval_to_milliseconds(interval: str) -> int:
    """
    Converte intervalli Binance in millisecondi.
    Per ora ci servono soprattutto '5m' e '1h'.
    """
    unit = interval[-1]
    value = int(interval[:-1])

    if unit == "m":
        return value * 60 * 1000

    if unit == "h":
        return value * 60 * 60 * 1000

    if unit == "d":
        return value * 24 * 60 * 60 * 1000

    raise ValueError(f"Intervallo non supportato: {interval}")


def download_binance_klines(
    symbol: str = "BTCUSDT",
    interval: str = "5m",
    start_date: str = "2024-01-01",
    end_date: str = "2024-02-01",
    sleep_seconds: float = 0.1,
) -> pd.DataFrame:
    """
    Scarica candele storiche da Binance e restituisce un DataFrame compatibile
    con il bot attuale:

    index datetime UTC
    open
    high
    low
    close
    volume
    """

    start_ms = _date_to_milliseconds(start_date)
    end_ms = _date_to_milliseconds(end_date)
    interval_ms = _interval_to_milliseconds(interval)

    all_rows = []
    current_ms = start_ms

    while current_ms < end_ms:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": current_ms,
            "endTime": end_ms,
            "limit": 1000,
        }

        url = f"{BINANCE_BASE_URL}/api/v3/klines?{urlencode(params)}"

        with urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        if not data:
            break

        all_rows.extend(data)

        last_open_time = data[-1][0]
        next_ms = last_open_time + interval_ms

        if next_ms <= current_ms:
            break

        current_ms = next_ms

        time.sleep(sleep_seconds)

    if not all_rows:
        raise ValueError(
            f"Nessun dato scaricato da Binance per {symbol} {interval} "
            f"da {start_date} a {end_date}"
        )

    df = pd.DataFrame(
        all_rows,
        columns=[
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base_volume",
            "taker_buy_quote_volume",
            "ignore",
        ],
    )

    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)

    df = df.set_index("open_time")

    df = df[["open", "high", "low", "close", "volume"]]

    df = df.astype(float)

    df = df[~df.index.duplicated(keep="first")]
    df = df.sort_index()

    start_dt = pd.to_datetime(start_date, utc=True)
    end_dt = pd.to_datetime(end_date, utc=True)

    df = df[
        (df.index >= start_dt) &
        (df.index < end_dt)
    ]

    return df