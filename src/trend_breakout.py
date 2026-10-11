from __future__ import annotations

import numpy as np
import pandas as pd


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close_prev = df["close"].shift(1)

    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean().fillna(0.0)


def compute_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-8)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def compute_moving_averages(df: pd.DataFrame, short_period: int = 20, long_period: int = 50) -> tuple[pd.Series, pd.Series]:
    short_ma = df["close"].rolling(window=short_period).mean()
    long_ma = df["close"].rolling(window=long_period).mean()
    return short_ma.fillna(df["close"]), long_ma.fillna(df["close"])


def is_pivot_high(series: pd.Series, idx: int, left: int = 3, right: int = 3) -> bool:
    if idx < left or idx >= len(series) - right:
        return False
    window = series.iloc[idx - left : idx + right + 1]
    return float(series.iloc[idx]) == float(window.max())


def is_pivot_low(series: pd.Series, idx: int, left: int = 3, right: int = 3) -> bool:
    if idx < left or idx >= len(series) - right:
        return False
    window = series.iloc[idx - left : idx + right + 1]
    return float(series.iloc[idx]) == float(window.min())


def compute_trend_levels(df: pd.DataFrame, lookback: int = 45, left: int = 3, right: int = 3) -> tuple[pd.Series, pd.Series]:
    highs = df["high"]
    lows = df["low"]

    high_pivots = []
    low_pivots = []

    for idx in range(len(df)):
        if is_pivot_high(highs, idx, left=left, right=right):
            high_pivots.append((idx, float(highs.iloc[idx])))
        if is_pivot_low(lows, idx, left=left, right=right):
            low_pivots.append((idx, float(lows.iloc[idx])))

    support = pd.Series(np.nan, index=df.index)
    resistance = pd.Series(np.nan, index=df.index)

    for idx in range(len(df)):
        recent_highs = [p for p in high_pivots if p[0] <= idx and idx - p[0] <= lookback]
        recent_lows = [p for p in low_pivots if p[0] <= idx and idx - p[0] <= lookback]

        if len(recent_highs) >= 2:
            x = np.array([p[0] for p in recent_highs], dtype=float)
            y = np.array([p[1] for p in recent_highs], dtype=float)
            try:
                slope, intercept = np.polyfit(x, y, 1)
                resistance.iloc[idx] = slope * idx + intercept
            except Exception:
                pass

        if len(recent_lows) >= 2:
            x = np.array([p[0] for p in recent_lows], dtype=float)
            y = np.array([p[1] for p in recent_lows], dtype=float)
            try:
                slope, intercept = np.polyfit(x, y, 1)
                support.iloc[idx] = slope * idx + intercept
            except Exception:
                pass

    return support, resistance


def add_breakout_signals(
    df: pd.DataFrame,
    lookback: int = 45,
    left: int = 3,
    right: int = 3,
    min_distance_pct: float = 0.01,
    volume_confirmation: bool = True,
    rsi_confirmation: bool = True,
    ma_filter: bool = True,
    volatility_filter: bool = True,
    ma_short_period: int = 20,
    ma_long_period: int = 50,
    min_volatility_ratio: float = 0.8,
    max_volatility_ratio: float = 2.5,
) -> pd.DataFrame:
    result = df.copy()
    result["atr"] = compute_atr(result, period=14)
    result["rsi"] = compute_rsi(result, period=14)

    ma_short, ma_long = compute_moving_averages(result, short_period=ma_short_period, long_period=ma_long_period)
    result["ma_short"] = ma_short
    result["ma_long"] = ma_long
    result["ma_uptrend"] = result["ma_short"] > result["ma_long"]

    volume_ma = result["volume"].rolling(window=20).mean()
    volume_std = result["volume"].rolling(window=20).std().fillna(0)
    result["volume_z"] = (result["volume"] - volume_ma) / (volume_std + 1e-8)

    atr_ma = result["atr"].rolling(window=20).mean().fillna(result["atr"])
    result["volatility_ratio"] = result["atr"] / (atr_ma + 1e-8)

    support, resistance = compute_trend_levels(result, lookback=lookback, left=left, right=right)
    result["support_line"] = support
    result["resistance_line"] = resistance

    prev_close = result["close"].shift(1)
    prev_support = result["support_line"].shift(1)
    prev_resistance = result["resistance_line"].shift(1)

    long_breakout = (
        (result["close"] > result["resistance_line"]) & (prev_close <= prev_resistance)
        & (result["close"] > result["resistance_line"] * (1 + min_distance_pct))
    )

    short_breakout = (
        (result["close"] < result["support_line"]) & (prev_close >= prev_support)
        & (result["close"] < result["support_line"] * (1 - min_distance_pct))
    )

    if volume_confirmation:
        long_breakout &= (result["volume_z"] > 0.5)
        short_breakout &= (result["volume_z"] > 0.5)

    if rsi_confirmation:
        long_breakout &= (result["rsi"] > 40) & (result["rsi"] < 80)
        short_breakout &= (result["rsi"] > 20) & (result["rsi"] < 60)

    if ma_filter:
        long_breakout &= result["ma_uptrend"]
        short_breakout &= ~result["ma_uptrend"]

    if volatility_filter:
        long_breakout &= (result["volatility_ratio"] >= min_volatility_ratio) & (result["volatility_ratio"] <= max_volatility_ratio)
        short_breakout &= (result["volatility_ratio"] >= min_volatility_ratio) & (result["volatility_ratio"] <= max_volatility_ratio)

    result["long_breakout"] = long_breakout.fillna(False)
    result["short_breakout"] = short_breakout.fillna(False)
    result["signal"] = 0
    result.loc[result["long_breakout"], "signal"] = 1
    result.loc[result["short_breakout"], "signal"] = -1
    return result
