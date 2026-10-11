# Trend-Line Breakout Bot

A research-focused Python bot that tests a trend-line breakout strategy on CSV-based OHLCV data.

## Overview

This project scans historical market data, detects support and resistance trend lines from pivots, and only trades when price breaks those levels with confirmation from:

- moving averages
- RSI
- ATR-based volatility checks
- ADX trend strength
- volume confirmation

It is designed for research and backtesting, not live brokerage execution.

## Project structure

- `main.py` - main runner
- `src/data_loader.py` - CSV loading and validation
- `src/trend_breakout.py` - pivot/trend-line breakout signal logic
- `src/strength_filters.py` - ADX, ATR, and trend filters
- `src/backtest.py` - backtest engine and trade statistics
- `scripts/generate_sample_data.py` - synthetic dataset generator

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_sample_data.py
python main.py --csv data/sample.csv
```

## Strategy summary

The bot evaluates breakout entries when price moves beyond a previously established trend line after confirmation from trend and momentum filters.

- Long entry: price breaks upper trend line with trend confirmation
- Short entry: price breaks lower trend line with trend confirmation
- Risk control: stop-loss and take-profit logic
- Performance metrics: return, drawdown, win rate, profit factor

## Notes

This is a research bot for exploring breakout behavior on historical data. It is not connected to any exchange or broker.
