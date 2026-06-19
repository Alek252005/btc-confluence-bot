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
    avg = data["result"].mean()

    print(
        f"{name} | Trade: {len(data)} | Profitto: {profit:.2f} | "
        f"Win rate: {wr:.2f}% | PF: {pf:.2f} | Avg trade: {avg:.2f}"
    )


def direction_setup_combo(row):
    direction = row["direction"]

    parts = []

    if direction == "LONG":
        if row.get("bullish_sweep", False):
            parts.append("bullish_sweep")
        if row.get("bullish_break_retest", False):
            parts.append("bullish_break_retest")
        if row.get("bullish_engulfing", False):
            parts.append("bullish_engulfing")
        if row.get("bullish_382_candle", False):
            parts.append("bullish_382")

    if direction == "SHORT":
        if row.get("bearish_sweep", False):
            parts.append("bearish_sweep")
        if row.get("bearish_break_retest", False):
            parts.append("bearish_break_retest")
        if row.get("bearish_engulfing", False):
            parts.append("bearish_engulfing")
        if row.get("bearish_382_candle", False):
            parts.append("bearish_382")

    if not parts:
        return "no_setup_saved"

    return " + ".join(parts)


def main():
    trades = pd.read_csv("trades.csv")

    if len(trades) == 0:
        print("trades.csv è vuoto")
        return

    trades["entry_time"] = pd.to_datetime(trades["entry_time"], utc=True, errors="coerce")
    trades["month"] = trades["entry_time"].dt.strftime("%Y-%m")
    trades["hour"] = trades["entry_time"].dt.hour

    trades["score_bucket"] = pd.cut(
        trades["signal_score"],
        bins=[-1, 79, 89, 99, 999],
        labels=["<80", "80-89", "90-99", "100+"]
    )

    trades["setup_combo"] = trades.apply(direction_setup_combo, axis=1)

    print("\n==============================")
    print("SCORE BUCKET GENERALE")
    print("==============================")
    for bucket, group in trades.groupby("score_bucket", observed=False):
        stats(f"Score {bucket}", group)

    print("\n==============================")
    print("SCORE 80-89: LONG VS SHORT")
    print("==============================")
    bucket_80 = trades[trades["score_bucket"] == "80-89"]
    stats("80-89 LONG", bucket_80[bucket_80["direction"] == "LONG"])
    stats("80-89 SHORT", bucket_80[bucket_80["direction"] == "SHORT"])

    print("\n==============================")
    print("SCORE 90-99: LONG VS SHORT")
    print("==============================")
    bucket_90 = trades[trades["score_bucket"] == "90-99"]
    stats("90-99 LONG", bucket_90[bucket_90["direction"] == "LONG"])
    stats("90-99 SHORT", bucket_90[bucket_90["direction"] == "SHORT"])

    print("\n==============================")
    print("SCORE 100+: LONG VS SHORT")
    print("==============================")
    bucket_100 = trades[trades["score_bucket"] == "100+"]
    stats("100+ LONG", bucket_100[bucket_100["direction"] == "LONG"])
    stats("100+ SHORT", bucket_100[bucket_100["direction"] == "SHORT"])

    print("\n==============================")
    print("SCORE 80-89: SETUP COMBO")
    print("==============================")
    combo_80 = (
        bucket_80
        .groupby(["direction", "setup_combo"])
        .agg(
            trades=("result", "count"),
            profit=("result", "sum"),
            win_rate=("result", lambda x: (x > 0).mean() * 100),
            avg_trade=("result", "mean"),
        )
        .sort_values("profit", ascending=False)
    )
    print(combo_80.to_string())

    print("\n==============================")
    print("SCORE 90-99: SETUP COMBO")
    print("==============================")
    combo_90 = (
        bucket_90
        .groupby(["direction", "setup_combo"])
        .agg(
            trades=("result", "count"),
            profit=("result", "sum"),
            win_rate=("result", lambda x: (x > 0).mean() * 100),
            avg_trade=("result", "mean"),
        )
        .sort_values("profit", ascending=False)
    )
    print(combo_90.to_string())

    print("\n==============================")
    print("SCORE 100+: SETUP COMBO")
    print("==============================")
    combo_100 = (
        bucket_100
        .groupby(["direction", "setup_combo"])
        .agg(
            trades=("result", "count"),
            profit=("result", "sum"),
            win_rate=("result", lambda x: (x > 0).mean() * 100),
            avg_trade=("result", "mean"),
        )
        .sort_values("profit", ascending=False)
    )
    print(combo_100.to_string())

    print("\n==============================")
    print("SCORE 80-89: PER MESE")
    print("==============================")
    for month, group in bucket_80.groupby("month"):
        stats(f"80-89 {month}", group)

    print("\n==============================")
    print("SCORE 80-89: PER ORA")
    print("==============================")
    for hour, group in bucket_80.groupby("hour"):
        stats(f"80-89 ora {hour:02d}:00", group)

    print("\n==============================")
    print("TOP 20 TRADE VINCENTI SCORE 80-89")
    print("==============================")
    print(
        bucket_80.sort_values("result", ascending=False)[
            [
                "entry_time",
                "direction",
                "signal_score",
                "result",
                "setup_combo",
                "bullish_sweep",
                "bearish_sweep",
                "bullish_break_retest",
                "bearish_break_retest",
                "bullish_engulfing",
                "bearish_engulfing",
                "bullish_382_candle",
                "bearish_382_candle",
            ]
        ].head(20).to_string(index=False)
    )

    print("\n==============================")
    print("TOP 20 TRADE PERDENTI SCORE 80-89")
    print("==============================")
    print(
        bucket_80.sort_values("result", ascending=True)[
            [
                "entry_time",
                "direction",
                "signal_score",
                "result",
                "setup_combo",
                "bullish_sweep",
                "bearish_sweep",
                "bullish_break_retest",
                "bearish_break_retest",
                "bullish_engulfing",
                "bearish_engulfing",
                "bullish_382_candle",
                "bearish_382_candle",
            ]
        ].head(20).to_string(index=False)
    )

    bucket_80.to_csv("score_80_89_trades.csv", index=False)
    print("\nCreato file: score_80_89_trades.csv")


if __name__ == "__main__":
    main()