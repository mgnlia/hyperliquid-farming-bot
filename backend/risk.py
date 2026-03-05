"""Risk manager utilities for simulated agent."""


class RiskManager:
    """Enforce drawdown and sizing limits."""

    def __init__(self, max_position_pct: float, max_drawdown_pct: float, kelly_fraction: float):
        self.max_position_pct = max_position_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.kelly_fraction = kelly_fraction

        self.peak_value = 0.0
        self.current_drawdown = 0.0

    def update_drawdown(self, portfolio_value: float) -> bool:
        if portfolio_value > self.peak_value:
            self.peak_value = portfolio_value
        if self.peak_value <= 0:
            self.current_drawdown = 0.0
        else:
            self.current_drawdown = max(0.0, (self.peak_value - portfolio_value) / self.peak_value)
        return self.current_drawdown <= self.max_drawdown_pct

    def kelly_size(self, win_prob: float, win_loss_ratio: float) -> float:
        if win_loss_ratio <= 0:
            return 0.0
        raw = win_prob - (1 - win_prob) / win_loss_ratio
        scaled = max(0.0, raw * self.kelly_fraction)
        return min(self.max_position_pct, scaled)

    def metrics(self) -> dict:
        return {
            "peak_value": round(self.peak_value, 2),
            "current_drawdown": round(self.current_drawdown, 4),
            "max_drawdown_pct": self.max_drawdown_pct,
            "max_position_pct": self.max_position_pct,
            "kelly_fraction": self.kelly_fraction,
            "is_halted": self.current_drawdown > self.max_drawdown_pct,
        }
