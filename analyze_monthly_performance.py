import pandas as pd


def stats(name, data):
    if len(data) == 0:
        print(f"{name} -> Nessun trade")
        return

    profit = data["result"].sum()
    wins = (data["result"] > 0).sum()
    losses = (data["result"] < 0).sum()

    gross_profit = data.loc[data["result"] > 0, "result"].sum()
    gross_loss = abs(data.loc[data["result"] < 0, "result"].sum())

    pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    wr = wins / len(data) * 100
    avg_trade = data["result"].mean()

    print(
        f"{name} | Trade: {len(data)} | Profitto: {profit:.2f} | "
        f"Win rate: {wr:.2f}% | PF: {pf:.2f} | Avg trade: {avg_trade:.2f}"
    )


def main():
    trades = pd.read_csv("trades.csv")

    trades["entry_time"] = pd.to_datetime(trades["entry_time"], utc=True)
    trades["month"] = trades["entry_time"].dt.strftime("%Y-%m")
    trades["hour"] = trades["entry_time"].dt.hour

    print("\n==============================")
    print("PERFORMANCE GENERALE")
    print("==============================")
    stats("Totale", trades)

    print("\n==============================")
    print("PERFORMANCE PER MESE")
    print("==============================")
    for month, group in trades.groupby("month"):
        stats(month, group)

    print("\n==============================")
    print("PERFORMANCE PER MESE E SETUP")
    print("==============================")
    for month, month_group in trades.groupby("month"):
        print(f"\n--- {month} ---")
        stats("Bearish 382", month_group[month_group["bearish_382_candle"] == True])
        stats("Bearish Engulfing", month_group[month_group["bearish_engulfing"] == True])
        stats("Bearish Break Retest", month_group[month_group["bearish_break_retest"] == True])
        stats("Bearish Sweep", month_group[month_group["bearish_sweep"] == True])

    print("\n==============================")
    print("PERFORMANCE PER ORA")
    print("==============================")
    for hour, group in trades.groupby("hour"):
        stats(f"Ora {hour:02d}:00", group)


if __name__ == "__main__":
    main()