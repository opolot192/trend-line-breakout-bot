from __future__ import annotations

import numpy as np
import pandas as pd


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (ATR)."""
    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr.fillna(0.0)


def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average Directional Index (ADX)."""
    high = df["high"]
    low = df["low"]
    close = df["close"]

    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr = compute_atr(df, period=period)
    plus_di = 100 * pd.Series(plus_dm).rolling(window=period).sum() / (tr.rolling(window=period).sum() + 1e-8)
    minus_di = 100 * pd.Series(minus_dm).rolling(window=period).sum() / (tr.rolling(window=period).sum() + 1e-8)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-8)
    adx = dx.rolling(window=period).mean()

    return adx.fillna(0.0)


def compute_moving_averages(df: pd.DataFrame, short_period: int = 20, long_period: int = 50) -> tuple[pd.Series, pd.Series]:
    """Compute SMA trend filter."""
    short_ma = df["close"].rolling(window=short_period).mean()
    long_ma = df["close"].rolling(window=long_period).mean()
    return short_ma.fillna(df["close"]), long_ma.fillna(df["close"])


def add_strength_filters(df: pd.DataFrame, adx_period: int = 14, min_adx: float = 20.0) -> pd.DataFrame:
    """Add ADX and trend strength filters to dataframe."""
    result = df.copy()
    result["atr"] = compute_atr(result, period=14)
    result["adx"] = compute_adx(result, period=adx_period)
    result["trend_strength_ok"] = result["adx"] >= min_adx
    return result
