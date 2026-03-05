"""Risk management module with Kelly sizing and position limits."""


class RiskManager:
    """Manages position sizing and drawdown limits."""

    def __init__(
        self,
        max_position_pct: float = 0.25,
        max_drawdown_pct: float = 0.15,
        kelly_fraction: float = 0.5,
    ):
        self.max_position_pct = max_position_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.kelly_fraction = kelly_fraction
        self.peak_value: float = 0.0
        self.current_drawdown: float = 0.0

    def kelly_size(self, win_prob: float, win_loss_ratio: float) -> float:
        """Calculate Kelly criterion position size."""
        if win_prob <= 0 or win_loss_ratio <= 0:
            return 0.0
        kelly = win_prob - (1 - win_prob) / win_loss_ratio
        kelly = max(0.0, kelly) * self.kelly_fraction
        return min(kelly, self.max_position_pct)

    def update_drawdown(self, portfolio_value: float) -> bool:
        """Update drawdown tracking. Returns True if within limits."""
        if portfolio_value > self.peak_value:
            self.peak_value = portfolio_value
        if self.peak_value > 0:
            self.current_drawdown = (self.peak_value - portfolio_value) / self.peak_value
        return self.current_drawdown < self.max_drawdown_pct

    def check_position_limit(self, position_value: float, portfolio_value: float) -> bool:
        """Check if a position is within the maximum allowed size."""
        if portfolio_value <= 0:
            return False
        return (position_value / portfolio_value) <= self.max_position_pct

    def max_position_value(self, portfolio_value: float) -> float:
        """Get the maximum allowed position value."""
        return portfolio_value * self.max_position_pct

    def is_halted(self) -> bool:
        """Check if trading should be halted due to drawdown."""
        return self.current_drawdown >= self.max_drawdown_pct

    def get_risk_metrics(self) -> dict:
        """Return current risk metrics."""
        return {
            "peak_value": round(self.peak_value, 2),
            "current_drawdown": round(self.current_drawdown, 4),
            "max_drawdown_pct": self.max_drawdown_pct,
            "max_position_pct": self.max_position_pct,
            "kelly_fraction": self.kelly_fraction,
            "is_halted": self.is_halted(),
        }
