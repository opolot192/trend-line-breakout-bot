from __future__ import annotations

import pandas as pd
import requests
from pathlib import Path
from typing import Optional


def download_binance_klines(
    symbol: str = "BTCUSDT",
    interval: str = "15m",
    start_date: str = "2024-01-01",
    end_date: str = "2024-10-01",
    output_dir: str = "data",
) -> str:
    """
    Download OHLCV data from Binance Vision (public data API).
    
    Args:
        symbol: Trading pair (e.g., BTCUSDT)
        interval: Timeframe (1m, 5m, 15m, 1h, etc.)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        output_dir: Directory to save CSV files
    
    Returns:
        Path to the saved CSV file
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    base_url = "https://data.binance.vision/api/v3/klines"
    
    start_ts = pd.Timestamp(start_date).value // 10**6
    end_ts = pd.Timestamp(end_date).value // 10**6
    
    all_data = []
    current_ts = start_ts
    
    print(f"Downloading {symbol} {interval} data from {start_date} to {end_date}...")
    
    while current_ts < end_ts:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": int(current_ts),
            "endTime": int(end_ts),
            "limit": 1000,
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                break
            
            all_data.extend(data)
            current_ts = data[-1][0] + 1
            print(f"  Downloaded {len(all_data)} candles so far...")
            
        except requests.exceptions.RequestException as e:
            print(f"Error downloading data: {e}")
            break
    
    if not all_data:
        raise ValueError("No data downloaded from Binance Vision")
    
    df = pd.DataFrame(all_data, columns=[\n        "timestamp", "open", "high", "low", "close", "volume",\n        "close_time", "quote_asset_volume", "number_of_trades",\n        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"\n    ])\n    
    df = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()\n    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")\n    
    for col in ["open", "high", "low", "close", "volume"]:\n        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df = df.dropna()
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    
    output_file = f"{output_dir}/{symbol}_{interval}_{start_date}_{end_date}.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\n✅ Downloaded {len(df)} candles and saved to {output_file}")
    return output_file


if __name__ == "__main__":
    # Download Bitcoin 15m data
    file_15m = download_binance_klines(
        symbol="BTCUSDT",
        interval="15m",
        start_date="2024-06-01",
        end_date="2024-10-11",
    )
    
    # Download Bitcoin 3m data
    file_3m = download_binance_klines(
        symbol="BTCUSDT",
        interval="3m",
        start_date="2024-06-01",
        end_date="2024-10-11",
    )
    
    print(f"\n📊 Ready to backtest:")
    print(f"  15m: {file_15m}")
    print(f"  3m: {file_3m}")
