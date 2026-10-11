from __future__ import annotations

from pathlib import Path

from src.data_loader import load_ohlcv_csv
from src.strength_filters import add_strength_filters
from src.trend_breakout import add_breakout_signals
from src.backtest import BacktestEngine


def main() -> None:
    csv_path = Path("data/sample.csv")
    df = load_ohlcv_csv(str(csv_path))
    df = add_strength_filters(df)
    df = add_breakout_signals(df)
    engine = BacktestEngine()
    _, trades, summary = engine.run(df)
    print(summary)
    print(f"Trades executed: {len(trades)}")


if __name__ == "__main__":
    main()
