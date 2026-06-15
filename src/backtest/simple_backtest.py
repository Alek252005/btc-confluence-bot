import pandas as pd


def run_backtest(
    df: pd.DataFrame,
    initial_balance: float = 1000.0,
    risk_per_trade: float = 0.01,
    atr_stop_multiplier: float = 1.0,
    atr_target_multiplier: float = 2.0,
    max_bars_in_trade: int = 50,
    use_ema20_trailing: bool = False,
    use_break_even: bool = False,
    break_even_at_r: float = 1.0,
) -> dict:
    balance = initial_balance
    trades = []

    i = 1

    while i < len(df) - max_bars_in_trade - 1:
        row = df.iloc[i]

        if not row["long_signal"] and not row["short_signal"]:
            i += 1
            continue

        entry_index = i + 1
        entry_row = df.iloc[entry_index]
        entry_price = entry_row["open"]
        atr = row["atr_14"]

        if atr <= 0:
            i += 1
            continue

        risk_amount = balance * risk_per_trade

        if row["long_signal"]:
            direction = "LONG"
            atr_stop = entry_price - (atr * atr_stop_multiplier)

            recent_swing_low = df["low"].where(df["swing_low"]).iloc[:i].dropna()

            if len(recent_swing_low) > 0:
                swing_stop = recent_swing_low.iloc[-1]
                stop_loss = min(atr_stop, swing_stop)
            else:
                stop_loss = atr_stop

            risk_per_unit = entry_price - stop_loss
            initial_risk_per_unit = risk_per_unit
            take_profit = entry_price + (risk_per_unit * atr_target_multiplier)

        else:
            direction = "SHORT"
            atr_stop = entry_price + (atr * atr_stop_multiplier)

            recent_swing_high = df["high"].where(df["swing_high"]).iloc[:i].dropna()

            if len(recent_swing_high) > 0:
                swing_stop = recent_swing_high.iloc[-1]
                stop_loss = max(atr_stop, swing_stop)
            else:
                stop_loss = atr_stop

            risk_per_unit = stop_loss - entry_price
            initial_risk_per_unit = risk_per_unit
            take_profit = entry_price - (risk_per_unit * atr_target_multiplier)

        outcome = None
        exit_price = None
        exit_time = None
        result = 0
        exit_index = None

        for j in range(entry_index, entry_index + max_bars_in_trade):
            future_row = df.iloc[j]

            if use_ema20_trailing and j > entry_index:
                if direction == "LONG":
                    ema_stop = future_row["ema_20"]

                    if ema_stop > stop_loss and ema_stop < future_row["close"]:
                        stop_loss = ema_stop

                else:
                    ema_stop = future_row["ema_20"]

                    if ema_stop < stop_loss and ema_stop > future_row["close"]:
                        stop_loss = ema_stop

            if direction == "LONG":
                stop_hit = future_row["low"] <= stop_loss
                target_hit = future_row["high"] >= take_profit

                if stop_hit and target_hit:
                    outcome = "LOSS"
                    exit_price = stop_loss
                    result = -risk_amount
                    exit_time = df.index[j]
                    exit_index = j
                    break

                if stop_hit:
                    outcome = "LOSS"
                    exit_price = stop_loss
                    result = -risk_amount
                    exit_time = df.index[j]
                    exit_index = j
                    break

                if target_hit:
                    outcome = "WIN"
                    exit_price = take_profit
                    result = risk_amount * atr_target_multiplier
                    exit_time = df.index[j]
                    exit_index = j
                    break

            else:
                stop_hit = future_row["high"] >= stop_loss
                target_hit = future_row["low"] <= take_profit

                if stop_hit and target_hit:
                    outcome = "LOSS"
                    exit_price = stop_loss
                    result = -risk_amount
                    exit_time = df.index[j]
                    exit_index = j
                    break

                if stop_hit:
                    outcome = "LOSS"
                    exit_price = stop_loss
                    result = -risk_amount
                    exit_time = df.index[j]
                    exit_index = j
                    break

                if target_hit:
                    outcome = "WIN"
                    exit_price = take_profit
                    result = risk_amount * atr_target_multiplier
                    exit_time = df.index[j]
                    exit_index = j
                    break

        if outcome is None:
            i += 1
            continue

        balance += result

        trades.append({
            "entry_time": df.index[entry_index],
            "exit_time": exit_time,
            "direction": direction,
            "entry": entry_price,
            "exit": exit_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "outcome": outcome,
            "result": result,
            "balance": balance,
        })

        # Salta direttamente a dopo la chiusura del trade
        i = exit_index + 1

    total_trades = len(trades)
    wins = sum(1 for t in trades if t["outcome"] == "WIN")
    losses = sum(1 for t in trades if t["outcome"] == "LOSS")

    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

    return {
        "initial_balance": initial_balance,
        "final_balance": balance,
        "profit": balance - initial_balance,
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "trades": trades,
    }