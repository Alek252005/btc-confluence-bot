import pandas as pd
import yfinance as yf

from src.features.feature_engine import add_indicators
from src.strategy.trend_strategy import generate_signals
from src.backtest.simple_backtest import run_backtest
from src.features.candlestick_patterns import add_candlestick_patterns
from src.features.market_structure import add_market_structure
from src.features.break_retest import add_break_retest
from src.features.higher_timeframe import get_h4_trend
from src.features.liquidity import (
    add_equal_highs_lows,
    add_liquidity_sweeps
)


def main():
    print("Scarico dati BTC...")

    # Scarica 30 giorni di dati BTC a 5 minuti
    df = yf.download(
        "BTC-USD",
        period="60d",
        interval="5m",
        auto_adjust=True,
        progress=False
    )

    # Gestisce le colonne MultiIndex di yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Rinomina le colonne in minuscolo
    df = df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })

    # Rimuove eventuali valori mancanti
    df = df.dropna()

    # Calcola gli indicatori
    df = add_indicators(df)

    h4 = get_h4_trend()

    h4 = h4.reindex(
        df.index,
        method="ffill"
    )

    df["h4_uptrend"] = h4["h4_uptrend"]
    df["h4_downtrend"] = h4["h4_downtrend"]

    df = add_market_structure(df)

    df = add_candlestick_patterns(df)

    df = add_break_retest(df)

    df = add_equal_highs_lows(df)

    df = add_liquidity_sweeps(df)

    



    # Genera i segnali LONG e SHORT
    df = generate_signals(df, trend_mode="hybrid")

    # Mostra le ultime 20 righe
    print("\nUltime 20 candele:")
    print(
        df[
            [
                "open",
                "high",
                "low",
                "close",
                "ema_20",
                "ema_50",
                "atr_14",
                "rsi_14",
                "long_signal",
                "short_signal",
                "ema_200",
                "long_score",
                "short_score",
                "equal_high",
                "equal_low",
                "bullish_sweep",
                "bearish_sweep",
            ]
        ].tail(20)
    )

    # Statistiche segnali
    print("\nSegnali LONG trovati:", int(df["long_signal"].sum()))
    print("Segnali SHORT trovati:", int(df["short_signal"].sum()))

    results = run_backtest(
        df,
        use_break_even=True
    )

    print("\n--- RISULTATI BACKTEST ---")
    print("Capitale iniziale:", results["initial_balance"])
    print("Capitale finale:", round(results["final_balance"], 2))
    print("Profitto:", round(results["profit"], 2))
    print("Trade totali:", results["total_trades"])
    print("Vinti:", results["wins"])
    print("Persi:", results["losses"])
    print("Win rate:", round(results["win_rate"], 2), "%")
    print("Profit Factor:", round(results["profit_factor"], 2))
    print("Average Win:", round(results["average_win"], 2))
    print("Average Loss:", round(results["average_loss"], 2))  
    print("Prima candela:", df.index[0])
    print("Ultima candela:", df.index[-1])
    print("Numero totale candele:", len(df)) 
    print("Swing High:", int(df["swing_high"].sum()))
    print("Swing Low:", int(df["swing_low"].sum()))
    print("Higher High:", int(df["higher_high"].sum()))
    print("Lower High:", int(df["lower_high"].sum()))
    print("Higher Low:", int(df["higher_low"].sum()))
    print("Lower Low:", int(df["lower_low"].sum()))
    print("Bullish engulfing:", df["bullish_engulfing"].sum())
    print("Bearish engulfing:", df["bearish_engulfing"].sum())
    print("Equal High:", int(df["equal_high"].sum()))
    print("Equal Low:", int(df["equal_low"].sum()))
    print("Bullish Sweep:", int(df["bullish_sweep"].sum()))
    print("Bearish Sweep:", int(df["bearish_sweep"].sum()))


if __name__ == "__main__":
    main()