import pandas as pd
from src.data.binance_data import download_binance_klines

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

SYMBOL = "BTCUSDT"

DATA_START = "2024-01-01"
TEST_START = "2024-06-01"
TEST_END = "2024-12-31"

INTERVAL = "5m"

def main():
    print("Scarico dati BTC da Binance...")

    test_start_dt = pd.to_datetime(TEST_START, utc=True)
    test_end_exclusive_dt = pd.to_datetime(TEST_END, utc=True) + pd.Timedelta(days=1)

    download_end = test_end_exclusive_dt.strftime("%Y-%m-%d")

    print("Symbol:", SYMBOL)
    print("DATA_START:", DATA_START)
    print("TEST_START:", TEST_START)
    print("TEST_END:", TEST_END)

    df = download_binance_klines(
        symbol=SYMBOL,
        interval=INTERVAL,
        start_date=DATA_START,
        end_date=download_end,
    )

    df = df.dropna()

    # Calcola gli indicatori
    df = add_indicators(df)

    h4 = get_h4_trend(
        start_date=DATA_START,
        end_date=download_end,
        symbol=SYMBOL,
    )

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

    test_mask = (
        (df.index >= test_start_dt) &
        (df.index < test_end_exclusive_dt)
    )

    df.loc[~test_mask, "long_signal"] = False
    df.loc[~test_mask, "short_signal"] = False

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

    trades_df = pd.DataFrame(results["trades"])
    trades_df.to_csv("trades.csv", index=False)

    print("File trades.csv creato con", len(trades_df), "trade")

    def analyze_group(name, data):
        if len(data) == 0:
            print(name, "-> Nessun trade")
            return

        profit = data["result"].sum()
        wins = (data["result"] > 0).sum()
        losses = (data["result"] < 0).sum()

        gross_profit = data.loc[data["result"] > 0, "result"].sum()
        gross_loss = abs(data.loc[data["result"] < 0, "result"].sum())

        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
        win_rate = wins / len(data) * 100

        print(
            name,
            "| Trade:", len(data),
            "| Profitto:", round(profit, 2),
            "| Win rate:", round(win_rate, 2), "%",
            "| PF:", round(profit_factor, 2)
        )


    print("\n--- ANALISI SETUP ---")

    analyze_group("Score 80-89", trades_df[(trades_df["signal_score"] >= 80) & (trades_df["signal_score"] < 90)])
    analyze_group("Score 90-99", trades_df[(trades_df["signal_score"] >= 90) & (trades_df["signal_score"] < 100)])
    analyze_group("Score 100+", trades_df[trades_df["signal_score"] >= 100])

    print("\n--- ANALISI LIQUIDITY ---")
    analyze_group("Bullish Sweep", trades_df[trades_df["bullish_sweep"] == True])
    analyze_group("Bearish Sweep", trades_df[trades_df["bearish_sweep"] == True])

    print("\n--- ANALISI BREAK RETEST ---")
    analyze_group("Bullish Break Retest", trades_df[trades_df["bullish_break_retest"] == True])
    analyze_group("Bearish Break Retest", trades_df[trades_df["bearish_break_retest"] == True])

    print("\n--- ANALISI CANDLE ---")
    analyze_group("Bullish Engulfing", trades_df[trades_df["bullish_engulfing"] == True])
    analyze_group("Bearish Engulfing", trades_df[trades_df["bearish_engulfing"] == True])
    analyze_group("Bullish 382 Candle", trades_df[trades_df["bullish_382_candle"] == True])
    analyze_group("Bearish 382 Candle", trades_df[trades_df["bearish_382_candle"] == True])

    print("\n--- ANALISI DIREZIONE ---")

    analyze_group(
        "LONG",
        trades_df[trades_df["direction"] == "LONG"]
    )

    analyze_group(
        "SHORT",
        trades_df[trades_df["direction"] == "SHORT"]
    )

    print("\n--- ANALISI LONG DETTAGLIATA ---")

    long_trades = trades_df[trades_df["direction"] == "LONG"]

    analyze_group("LONG con Bullish Engulfing", long_trades[long_trades["bullish_engulfing"] == True])
    analyze_group("LONG senza Bullish Engulfing", long_trades[long_trades["bullish_engulfing"] == False])

    analyze_group("LONG con Bullish 382", long_trades[long_trades["bullish_382_candle"] == True])
    analyze_group("LONG senza Bullish 382", long_trades[long_trades["bullish_382_candle"] == False])

    analyze_group("LONG con Bullish Break Retest", long_trades[long_trades["bullish_break_retest"] == True])
    analyze_group("LONG senza Bullish Break Retest", long_trades[long_trades["bullish_break_retest"] == False])

    analyze_group("LONG con Bullish Sweep", long_trades[long_trades["bullish_sweep"] == True])
    analyze_group("LONG senza Bullish Sweep", long_trades[long_trades["bullish_sweep"] == False])

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
    print("Bullish Break Retest:", int(df["bullish_break_retest"].sum()))
    print("Bearish Break Retest:", int(df["bearish_break_retest"].sum()))
    print("Equal High:", int(df["equal_high"].sum()))
    print("Equal Low:", int(df["equal_low"].sum()))
    print("Bullish Sweep:", int(df["bullish_sweep"].sum()))
    print("Bearish Sweep:", int(df["bearish_sweep"].sum()))


if __name__ == "__main__":
    main()