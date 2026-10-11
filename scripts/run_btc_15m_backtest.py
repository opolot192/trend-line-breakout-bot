from __future__ import annotations

import requests
import pandas as pd
from pathlib import Path


def download_binance_klines(
    symbol: str = "BTCUSDT",
    interval: str = "15m",
    start_date: str = "2024-01-01",
    end_date: str = "2024-10-11",
    output_dir: str = "data",
) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    base_url = "https://data.binance.vision/api/v3/klines"
    start_ts = int(pd.Timestamp(start_date).timestamp() * 1000)
    end_ts = int(pd.Timestamp(end_date).timestamp() * 1000)

    all_rows = []
    current_ts = start_ts

    while current_ts < end_ts:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": current_ts,
            "endTime": end_ts,
            "limit": 1000,
        }
        response = requests.get(base_url, params=params, timeout=20)
        response.raise_for_status()
        rows = response.json()
        if not rows:
            break
        all_rows.extend(rows)
        current_ts = int(rows[-1][0]) + 1

    if not all_rows:
        raise ValueError("No Binance data downloaded.")

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
            "quote_volume",
            "trades",
            "taker_buy_base",
            "taker_buy_quote",
            "ignore",
        ],
    )
    df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms")
    df = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna().sort_values("timestamp").reset_index(drop=True)

    output_path = f"{output_dir}/{symbol}_{interval}.csv"
    df.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    csv_path = download_binance_klines(symbol="BTCUSDT", interval="15m", start_date="2024-01-01", end_date="2024-10-11")
    print(f"Downloaded BTCUSDT 15m data to: {csv_path}")
    print("Run: python main.py --csv data/BTCUSDT_15m.csv --stop-loss-pct 0.01 --risk-reward-ratio 2")
