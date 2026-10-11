from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path


def generate_sample_data(path: str = "data/sample.csv", rows: int = 800) -> None:
    rng = np.random.default_rng(42)
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    price = 100.0
    data = []
    trend = [0.04, -0.03, 0.05, -0.02, 0.03]

    for i in range(rows):
        drift = trend[i % len(trend)]
        price *= 1 + rng.normal(drift, 0.02)
        open_price = price * (1 + rng.normal(0.0, 0.008))
        close_price = price * (1 + rng.normal(0.0, 0.01))
        high_price = max(open_price, close_price) * (1 + rng.uniform(0.006, 0.025))
        low_price = min(open_price, close_price) * (1 - rng.uniform(0.006, 0.02))
        volume = int(rng.integers(1000, 8000))

        timestamp = pd.Timestamp("2024-01-01") + pd.Timedelta(hours=i)
        data.append({
            "timestamp": timestamp,
            "open": round(float(open_price), 4),
            "high": round(float(high_price), 4),
            "low": round(float(low_price), 4),
            "close": round(float(close_price), 4),
            "volume": int(volume),
        })

    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows to {path}")


if __name__ == "__main__":
    generate_sample_data()
