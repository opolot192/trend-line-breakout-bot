from __future__ import annotations

import argparse
from pathlib import Path

from src.data_loader import load_ohlcv_csv
from src.strength_filters import add_strength_filters
from src.trend_breakout import add_breakout_signals
from src.backtest import BacktestEngine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Advanced BTC trend-line breakout strategy on 15m Binance data.")
    parser.add_argument("--csv", type=str, required=True, help="Path to BTCUSDT OHLCV CSV file.")
    parser.add_argument("--initial-capital", type=float, default=10000.0)
    parser.add_argument("--position-fraction", type=float, default=0.15)
    parser.add_argument("--stop-loss-pct", type=float, default=0.01, help="Risk per trade: 1% default")
    parser.add_argument("--risk-reward-ratio", type=float, default=2.0, help="Use 1:2 risk-to-reward")
    parser.add_argument("--lookback", type=int, default=45)
    parser.add_argument("--min-distance-pct", type=float, default=0.005)
    parser.add_argument("--short-ma", type=int, default=20)
    parser.add_argument("--long-ma", type=int, default=50)
    parser.add_argument("--min-adx", type=float, default=20.0)
    parser.add_argument("--min-volatility-ratio", type=float, default=0.8)
    parser.add_argument("--max-volatility-ratio", type=float, default=2.5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_ohlcv_csv(args.csv)
    df = add_strength_filters(df, min_adx=args.min_adx)
    df = add_breakout_signals(
        df,
        lookback=args.lookback,
        min_distance_pct=args.min_distance_pct,
        ma_short_period=args.short_ma,
        ma_long_period=args.long_ma,
        min_volatility_ratio=args.min_volatility_ratio,
        max_volatility_ratio=args.max_volatility_ratio,
    )

    engine = BacktestEngine(
        initial_capital=args.initial_capital,
        position_fraction=args.position_fraction,
        stop_loss_pct=args.stop_loss_pct,
        risk_reward_ratio=args.risk_reward_ratio,
    )

    _, trades, summary = engine.run(df)
    print("\nBTC 15m Breakout Backtest")
    print("=" * 60)
    for k, v in summary.items():
        print(f"{k}: {v}")
    print(f"Trades executed: {len(trades)}")


if __name__ == "__main__":
    main()
