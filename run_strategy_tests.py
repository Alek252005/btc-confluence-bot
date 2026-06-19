import math
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from src.backtest.simple_backtest import run_backtest
from src.data.binance_data import download_binance_klines
from src.features.break_retest import add_break_retest
from src.features.candlestick_patterns import add_candlestick_patterns
from src.features.feature_engine import add_indicators
from src.features.higher_timeframe import get_h4_trend
from src.features.liquidity import add_equal_highs_lows, add_liquidity_sweeps
from src.features.market_structure import add_market_structure
from src.strategy.trend_strategy import generate_signals


SYMBOL = "BTCUSDT"
INTERVAL = "5m"

DATA_START = "2024-12-01"
DATA_END = "2026-06-16"


@dataclass(frozen=True)
class TestPeriod:
    name: str
    start: str
    end: str


@dataclass(frozen=True)
class StrategyTestConfig:
    name: str
    signal_mode: str = "baseline"
    short_only: bool = True
    min_short_score: Optional[int] = None
    max_short_score: Optional[int] = None
    required_short_setup: Optional[str] = None


TEST_PERIODS = [
    TestPeriod("2025", "2025-01-01", "2025-12-31"),
    TestPeriod("2026", "2026-01-01", "2026-06-15"),
    TestPeriod("2025-2026", "2025-01-01", "2026-06-15"),
]


TEST_CONFIGS = [
    StrategyTestConfig(
        name="SHORT 80-89",
        signal_mode="baseline",
        min_short_score=80,
        max_short_score=89,
    ),
    StrategyTestConfig(
        name="SHORT 90-99",
        signal_mode="baseline",
        min_short_score=90,
        max_short_score=99,
    ),
    StrategyTestConfig(
        name="SHORT 80-99",
        signal_mode="baseline",
        min_short_score=80,
        max_short_score=99,
    ),
    StrategyTestConfig(
        name="SHORT 100+",
        signal_mode="baseline",
        min_short_score=100,
        max_short_score=None,
    ),
    StrategyTestConfig(
        name="SHORT 80-89 solo bearish 382",
        signal_mode="baseline",
        min_short_score=80,
        max_short_score=89,
        required_short_setup="bearish_382_candle",
    ),
    StrategyTestConfig(
        name="SHORT 80-89 solo bearish engulfing",
        signal_mode="baseline",
        min_short_score=80,
        max_short_score=89,
        required_short_setup="bearish_engulfing",
    ),
    StrategyTestConfig(
        name="SHORT 80-89 solo bearish break retest",
        signal_mode="baseline",
        min_short_score=80,
        max_short_score=89,
        required_short_setup="bearish_break_retest",
    ),
    StrategyTestConfig(
        name="SCORELESS bearish 382 pullback light",
        signal_mode="scoreless_bearish_382_pullback_light",
    ),
    StrategyTestConfig(
        name="SCORELESS bearish 382 pullback strict",
        signal_mode="scoreless_bearish_382_pullback_strict",
    ),
    StrategyTestConfig(
        name="SCORELESS bearish break retest",
        signal_mode="scoreless_bearish_break_retest",
    ),
    StrategyTestConfig(
        name="SCORELESS liquidity sweep rejection",
        signal_mode="scoreless_liquidity_sweep_rejection",
    ),
    StrategyTestConfig(
        name="SCORELESS strict professional confluence",
        signal_mode="scoreless_strict_professional_confluence",
    ),
]


def prepare_dataset() -> pd.DataFrame:
    print("Scarico dati BTC da Binance...")
    print("Symbol:", SYMBOL)
    print("DATA_START:", DATA_START)
    print("DATA_END:", DATA_END)

    df = download_binance_klines(
        symbol=SYMBOL,
        interval=INTERVAL,
        start_date=DATA_START,
        end_date=DATA_END,
    )

    df = df.dropna()
    df = add_indicators(df)

    h4 = get_h4_trend(
        start_date=DATA_START,
        end_date=DATA_END,
        symbol=SYMBOL,
    )

    h4 = h4.reindex(df.index, method="ffill")

    df["h4_uptrend"] = h4["h4_uptrend"]
    df["h4_downtrend"] = h4["h4_downtrend"]

    df = add_market_structure(df)
    df = add_candlestick_patterns(df)
    df = add_break_retest(df)
    df = add_equal_highs_lows(df)
    df = add_liquidity_sweeps(df)
    df = generate_signals(df, trend_mode="hybrid")

    return df


def apply_period_filter(df: pd.DataFrame, period: TestPeriod) -> pd.DataFrame:
    filtered = df.copy()

    start_dt = pd.to_datetime(period.start, utc=True)
    end_exclusive_dt = pd.to_datetime(period.end, utc=True) + pd.Timedelta(days=1)

    test_mask = (filtered.index >= start_dt) & (filtered.index < end_exclusive_dt)

    filtered.loc[~test_mask, "long_signal"] = False
    filtered.loc[~test_mask, "short_signal"] = False

    return filtered


def bool_column(df: pd.DataFrame, column: str, default: bool = False) -> pd.Series:
    if column not in df.columns:
        return pd.Series(default, index=df.index)

    return df[column].fillna(False).astype(bool)


def optional_condition(
    df: pd.DataFrame,
    required_columns: list[str],
    condition_builder,
) -> pd.Series:
    if all(column in df.columns for column in required_columns):
        condition = condition_builder(df)
        return condition.fillna(False).astype(bool)

    return pd.Series(True, index=df.index)


def build_scoreless_short_signal(
    df: pd.DataFrame,
    signal_mode: str,
) -> pd.Series:
    h4_downtrend = bool_column(df, "h4_downtrend")
    bearish_382 = bool_column(df, "bearish_382_candle")
    bearish_engulfing = bool_column(df, "bearish_engulfing")
    bearish_break_retest = bool_column(df, "bearish_break_retest")
    bearish_sweep = bool_column(df, "bearish_sweep")
    lower_high = bool_column(df, "lower_high")
    lower_low = bool_column(df, "lower_low")

    ema20_below_ema50 = optional_condition(
        df,
        ["ema_20", "ema_50"],
        lambda data: data["ema_20"] < data["ema_50"],
    )
    ema50_below_ema200 = optional_condition(
        df,
        ["ema_50", "ema_200"],
        lambda data: data["ema_50"] < data["ema_200"],
    )
    close_below_ema20 = optional_condition(
        df,
        ["close", "ema_20"],
        lambda data: data["close"] < data["ema_20"],
    )
    pullback_to_ema = optional_condition(
        df,
        ["high", "ema_20", "ema_50"],
        lambda data: (
            (data["high"] >= data["ema_20"]) |
            (data["high"] >= data["ema_50"])
        ),
    )
    anti_chase = optional_condition(
        df,
        ["ema_20", "close", "atr_14"],
        lambda data: (data["ema_20"] - data["close"]) <= (data["atr_14"] * 1.5),
    )
    recent_bearish_structure = lower_high | lower_low

    if signal_mode == "scoreless_bearish_382_pullback_light":
        return (
            h4_downtrend &
            ema20_below_ema50 &
            close_below_ema20 &
            pullback_to_ema &
            bearish_382
        )

    if signal_mode == "scoreless_bearish_382_pullback_strict":
        return (
            h4_downtrend &
            ema20_below_ema50 &
            ema50_below_ema200 &
            close_below_ema20 &
            pullback_to_ema &
            bearish_382 &
            anti_chase
        )

    if signal_mode == "scoreless_bearish_break_retest":
        return (
            h4_downtrend &
            recent_bearish_structure &
            bearish_break_retest &
            (bearish_engulfing | close_below_ema20)
        )

    if signal_mode == "scoreless_liquidity_sweep_rejection":
        return (
            h4_downtrend &
            bearish_sweep &
            (bearish_engulfing | bearish_382) &
            anti_chase
        )

    if signal_mode == "scoreless_strict_professional_confluence":
        return (
            h4_downtrend &
            ema20_below_ema50 &
            close_below_ema20 &
            recent_bearish_structure &
            pullback_to_ema &
            (bearish_382 | bearish_engulfing | bearish_break_retest) &
            anti_chase
        )

    raise ValueError(f"signal_mode non supportato: {signal_mode}")


def apply_config_filter(
    df: pd.DataFrame,
    config: StrategyTestConfig,
) -> pd.DataFrame:
    filtered = df.copy()

    if config.signal_mode != "baseline":
        filtered["long_signal"] = False
        filtered["short_signal"] = build_scoreless_short_signal(
            filtered,
            config.signal_mode,
        )
        return filtered

    if config.short_only:
        filtered["long_signal"] = False

    if config.min_short_score is not None:
        filtered["short_signal"] = (
            filtered["short_signal"] &
            (filtered["short_score"] >= config.min_short_score)
        )

    if config.max_short_score is not None:
        filtered["short_signal"] = (
            filtered["short_signal"] &
            (filtered["short_score"] <= config.max_short_score)
        )

    if config.required_short_setup is not None:
        filtered["short_signal"] = (
            filtered["short_signal"] &
            filtered[config.required_short_setup].fillna(False).astype(bool)
        )

    return filtered


def run_single_test(
    base_df: pd.DataFrame,
    config: StrategyTestConfig,
    period: TestPeriod,
) -> dict:
    df = apply_config_filter(base_df, config)
    df = apply_period_filter(df, period)

    results = run_backtest(
        df,
        use_break_even=True,
    )

    return {
        "config": config.name,
        "signal_mode": config.signal_mode,
        "periodo": period.name,
        "profitto": results["profit"],
        "capitale_finale": results["final_balance"],
        "trade": results["total_trades"],
        "win_rate": results["win_rate"],
        "profit_factor": results["profit_factor"],
        "average_win": results["average_win"],
        "average_loss": results["average_loss"],
    }


def format_number(value: float) -> str:
    if isinstance(value, float) and math.isinf(value):
        return "inf"

    return f"{value:.2f}"


def print_results_table(rows: list[dict]) -> None:
    columns = [
        ("config", "Configurazione"),
        ("signal_mode", "Signal mode"),
        ("periodo", "Periodo"),
        ("profitto", "Profitto"),
        ("capitale_finale", "Capitale finale"),
        ("trade", "Trade"),
        ("win_rate", "Win rate %"),
        ("profit_factor", "Profit factor"),
        ("average_win", "Average win"),
        ("average_loss", "Average loss"),
    ]

    formatted_rows = []

    for row in rows:
        formatted_rows.append({
            "config": row["config"],
            "signal_mode": row["signal_mode"],
            "periodo": row["periodo"],
            "profitto": format_number(row["profitto"]),
            "capitale_finale": format_number(row["capitale_finale"]),
            "trade": str(row["trade"]),
            "win_rate": format_number(row["win_rate"]),
            "profit_factor": format_number(row["profit_factor"]),
            "average_win": format_number(row["average_win"]),
            "average_loss": format_number(row["average_loss"]),
        })

    widths = {
        key: max(len(label), *(len(row[key]) for row in formatted_rows))
        for key, label in columns
    }

    header = " | ".join(
        label.ljust(widths[key])
        for key, label in columns
    )
    separator = "-+-".join("-" * widths[key] for key, _ in columns)

    print()
    print(header)
    print(separator)

    for row in formatted_rows:
        print(
            " | ".join(
                row[key].rjust(widths[key])
                if key not in {"config", "signal_mode", "periodo"}
                else row[key].ljust(widths[key])
                for key, _ in columns
            )
        )


def main() -> None:
    base_df = prepare_dataset()
    rows = []

    for config in TEST_CONFIGS:
        for period in TEST_PERIODS:
            print(f"Eseguo test: {config.name} | {period.name}")
            rows.append(run_single_test(base_df, config, period))

    print_results_table(rows)


if __name__ == "__main__":
    main()
