from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd


@dataclass
class BacktestTrade:
    side: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    pnl: float
    reason: str


class BacktestEngine:
    def __init__(
        self,
        initial_capital: float = 10000.0,
        position_fraction: float = 0.15,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.05,
        transaction_cost_pct: float = 0.0005,
    ) -> None:
        self.initial_capital = initial_capital
        self.position_fraction = position_fraction
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.transaction_cost_pct = transaction_cost_pct

    def run(self, df: pd.DataFrame) -> tuple[pd.DataFrame, List[BacktestTrade], dict]:
        cash = self.initial_capital
        position_units = 0.0
        entry_price = 0.0
        side = None
        entry_time = None
        trades: List[BacktestTrade] = []
        equity_curve = []

        for idx, row in df.iterrows():
            equity = cash + position_units * row["close"]
            equity_curve.append({"timestamp": row["timestamp"], "equity": equity})

            if side is None:
                if row["signal"] == 1:
                    capital = equity * self.position_fraction
                    position_units = capital / row["close"]
                    cash -= position_units * row["close"] * (1 + self.transaction_cost_pct)
                    entry_price = row["close"]
                    side = "long"
                    entry_time = row["timestamp"]
                elif row["signal"] == -1:
                    capital = equity * self.position_fraction
                    position_units = capital / row["close"]
                    cash -= position_units * row["close"] * (1 + self.transaction_cost_pct)
                    entry_price = row["close"]
                    side = "short"
                    entry_time = row["timestamp"]
                continue

            if side == "long":
                stop = entry_price * (1 - self.stop_loss_pct)
                target = entry_price * (1 + self.take_profit_pct)
                exit_price = None
                exit_reason = None

                if row["low"] <= stop:
                    exit_price = stop
                    exit_reason = "stop_loss"
                elif row["high"] >= target:
                    exit_price = target
                    exit_reason = "take_profit"
                elif row["signal"] == -1:
                    exit_price = row["close"]
                    exit_reason = "trend_reversal"

                if exit_price is not None:
                    pnl = position_units * (exit_price - entry_price) - position_units * exit_price * self.transaction_cost_pct
                    cash += position_units * exit_price * (1 - self.transaction_cost_pct)
                    trades.append(
                        BacktestTrade(
                            side=side,
                            entry_time=str(entry_time),
                            exit_time=str(row["timestamp"]),
                            entry_price=float(entry_price),
                            exit_price=float(exit_price),
                            pnl=float(pnl),
                            reason=exit_reason,
                        )
                    )
                    position_units = 0.0
                    entry_price = 0.0
                    side = None
                    entry_time = None

            elif side == "short":
                stop = entry_price * (1 + self.stop_loss_pct)
                target = entry_price * (1 - self.take_profit_pct)
                exit_price = None
                exit_reason = None

                if row["high"] >= stop:
                    exit_price = stop
                    exit_reason = "stop_loss"
                elif row["low"] <= target:
                    exit_price = target
                    exit_reason = "take_profit"
                elif row["signal"] == 1:
                    exit_price = row["close"]
                    exit_reason = "trend_reversal"

                if exit_price is not None:
                    pnl = position_units * (entry_price - exit_price) - position_units * exit_price * self.transaction_cost_pct
                    cash += position_units * exit_price * (1 - self.transaction_cost_pct)
                    trades.append(
                        BacktestTrade(
                            side=side,
                            entry_time=str(entry_time),
                            exit_time=str(row["timestamp"]),
                            entry_price=float(entry_price),
                            exit_price=float(exit_price),
                            pnl=float(pnl),
                            reason=exit_reason,
                        )
                    )
                    position_units = 0.0
                    entry_price = 0.0
                    side = None
                    entry_time = None

        final_equity = cash
        profit_series = np.array([t.pnl for t in trades], dtype=float)
        total_return = (final_equity - self.initial_capital) / self.initial_capital
        win_rate = float(np.mean(profit_series > 0)) if len(profit_series) else 0.0

        equity_df = pd.DataFrame(equity_curve)
        if len(profit_series) > 0:
            gains = profit_series[profit_series > 0]
            losses = -profit_series[profit_series < 0]
            profit_factor = float(np.sum(gains) / (np.sum(losses) + 1e-8))
            avg_trade = float(np.mean(profit_series))
        else:
            profit_factor = 0.0
            avg_trade = 0.0

        peak = equity_df["equity"].expanding().max()
        drawdown = (equity_df["equity"] - peak) / peak
        max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0

        summary = {
            "initial_capital": float(self.initial_capital),
            "final_equity": round(float(final_equity), 2),
            "total_return": round(float(total_return), 4),
            "total_trades": len(trades),
            "win_rate": round(float(win_rate), 4),
            "average_trade": round(float(avg_trade), 2),
            "max_drawdown": round(float(max_drawdown) * 100, 2),
            "profit_factor": round(float(profit_factor), 2),
        }
        return equity_df, trades, summary
