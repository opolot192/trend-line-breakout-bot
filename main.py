from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.data_loader import load_ohlcv_csv
from src.trend_breakout import add_breakout_signals
from src.strength_filters import add_strength_filters
from main_backtest import BacktestEngine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Advanced trend-line breakout strategy with ADX, MA, and ATR filters.")
    parser.add_argument("--csv", type=str, required=True, help="Path to OHLCV CSV file.")
    parser.add_argument("--initial-capital", type=float, default=10000.0, help="Starting account balance.")
    parser.add_argument("--position-fraction", type=float, default=0.15, help="Percent of equity used per trade.")
    parser.add_argument("--stop-loss-pct", type=float, default=0.02, help="Stop loss percentage.")
    parser.add_argument("--take-profit-pct", type=float, default=0.05, help="Take profit percentage.")
    parser.add_argument("--lookback", type=int, default=45, help="Lookback window for trend detection.")
    parser.add_argument("--min-distance-pct", type=float, default=0.01, help="Minimum distance from trend line.")
    parser.add_argument("--volume-confirmation", action="store_true", default=True, help="Require above-average volume.")
    parser.add_argument("--rsi-confirmation", action="store_true", default=True, help="Require RSI momentum confirmation.")
    parser.add_argument("--ma-filter", action="store_true", default=True, help="Require moving average trend alignment.")
    parser.add_argument("--volatility-filter", action="store_true", default=True, help="Require volatility to be in a healthy range.")
    parser.add_argument("--adx-filter", action="store_true", default=True, help="Require ADX trend strength.")
    parser.add_argument("--short-ma", type=int, default=20, help="Short moving average period.")
    parser.add_argument("--long-ma", type=int, default=50, help="Long moving average period.")
    parser.add_argument("--min-volatility-ratio", type=float, default=0.8, help="Minimum ATR-to-average ratio.")
    parser.add_argument("--max-volatility-ratio", type=float, default=2.5, help="Maximum ATR-to-average ratio.")
    parser.add_argument("--min-adx", type=float, default=20.0, help="Minimum ADX for trend confirmation.")
    parser.add_argument("--output-trades", type=str, default="trades.json", help="Save trade log to file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("\n" + "="*60)
    print("ADVANCED TREND-LINE BREAKOUT BOT")
    print("="*60)
    print(f"Loading CSV: {args.csv}")

    df = load_ohlcv_csv(args.csv)
    print(f"Loaded {len(df)} candles from {df['timestamp'].min()} to {df['timestamp'].max()}")

    print("\nAdding strength filters...")
    df = add_strength_filters(df, adx_period=14, min_adx=args.min_adx)

    print("\nDetecting trend lines and breakout signals...")
    df = add_breakout_signals(
        df,
        lookback=args.lookback,
        min_distance_pct=args.min_distance_pct,
        volume_confirmation=args.volume_confirmation,
        rsi_confirmation=args.rsi_confirmation,
        ma_filter=args.ma_filter,
        volatility_filter=args.volatility_filter,
        ma_short_period=args.short_ma,
        ma_long_period=args.long_ma,
        min_volatility_ratio=args.min_volatility_ratio,
        max_volatility_ratio=args.max_volatility_ratio,
    )

    if args.adx_filter:
        df["long_breakout"] = df["long_breakout"] & df["trend_strength_ok"]
        df["short_breakout"] = df["short_breakout"] & df["trend_strength_ok"]
        df["signal"] = 0
        df.loc[df["long_breakout"], "signal"] = 1
        df.loc[df["short_breakout"], "signal"] = -1

    long_signals = df[df["long_breakout"]].shape[0]
    short_signals = df[df["short_breakout"]].shape[0]
    print(f"Found {long_signals} long signals and {short_signals} short signals.")

    print("\nRunning backtest...")
    engine = BacktestEngine(
        initial_capital=args.initial_capital,
        position_fraction=args.position_fraction,
        stop_loss_pct=args.stop_loss_pct,
        take_profit_pct=args.take_profit_pct,
    )

    _, trades, summary = engine.run(df)

    print("\n" + "="*60)
    print("BACKTEST RESULTS")
    print("="*60)
    print(f"Initial Capital: ${summary['initial_capital']:,.2f}")
    print(f"Final Equity: ${summary['final_equity']:,.2f}")
    print(f"Total Return: {summary['total_return']*100:.2f}%")
    print(f"Total Trades: {summary['total_trades']}")
    print(f"Win Rate: {summary['win_rate']*100:.2f}%")
    print(f"Avg Trade P&L: ${summary['average_trade']:,.2f}")
    print(f"Max Drawdown: {summary['max_drawdown']*100:.2f}%")
    print(f"Profit Factor: {summary['profit_factor']:.2f}")
    print(f"Sharpe Ratio: {summary['sharpe_ratio']:.2f}")
    print(f"Win/Loss Ratio: {summary['win_loss_ratio']:.2f}")
    print("="*60)

    if trades:
        print(f"\n📊 Last 10 Trades:")
        for i, trade in enumerate(trades[-10:], 1):
            direction = "📈 LONG" if trade.side == "long" else "📉 SHORT"
            status = "✅" if trade.pnl > 0 else "❌"
            print(
                f"{i:2d}. {direction} | {trade.entry_time[:16]} | "
                f"Entry: ${trade.entry_price:.4f}, Exit: ${trade.exit_price:.4f} | "
                f"P&L: {status} ${trade.pnl:+.2f} | {trade.reason}"
            )
    else:
        print("\n⚠️ No trades were executed.")

    if trades and args.output_trades:
        trades_list = []
        for trade in trades:
            trades_list.append({
                "side": trade.side,
                "entry_time": str(trade.entry_time),
                "exit_time": str(trade.exit_time),
                "entry_price": round(trade.entry_price, 6),
                "exit_price": round(trade.exit_price, 6),
                "pnl": round(trade.pnl, 4),
                "reason": trade.reason,
            })

        output_path = Path(args.output_trades)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump({
                "summary": summary,
                "trades": trades_list,
            }, f, indent=2)

        print(f"\n💾 Trade log saved to {args.output_trades}")


if __name__ == "__main__":
    main()
