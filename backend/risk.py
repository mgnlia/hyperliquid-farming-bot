"""Risk management module with Kelly sizing, drawdown limits, and daily loss cap."""


class RiskManager:
    """Manages position sizing and drawdown limits."""

    def __init__(
        self,
        max_position_pct: float = 0.25,
        max_drawdown_pct: float = 0.15,
        kelly_fraction: float = 0.5,
        daily_loss_cap_usd: float = 500.0,
    ):
        self.max_position_pct = max_position_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.kelly_fraction = kelly_fraction
        self.daily_loss_cap_usd = daily_loss_cap_usd

        self.peak_value: float = 0.0
        self.current_drawdown: float = 0.0
        self.daily_loss_usd: float = 0.0

    def kelly_size(self, win_prob: float, win_loss_ratio: float) -> float:
        """Calculate Kelly criterion position size, capped at max_position_pct."""
        if win_prob <= 0 or win_loss_ratio <= 0:
            return 0.0
        kelly = win_prob - (1 - win_prob) / win_loss_ratio
        kelly = max(0.0, kelly) * self.kelly_fraction
        return min(kelly, self.max_position_pct)

    def update_drawdown(self, portfolio_value: float) -> bool:
        """Update drawdown tracking. Returns True if within limits (not halted)."""
        if portfolio_value > self.peak_value:
            self.peak_value = portfolio_value
        if self.peak_value > 0:
            self.current_drawdown = (self.peak_value - portfolio_value) / self.peak_value
        return self.current_drawdown < self.max_drawdown_pct

    def record_loss(self, loss_usd: float) -> bool:
        """Record a realized loss. Returns True if still within daily cap."""
        if loss_usd < 0:
            self.daily_loss_usd += loss_usd  # loss_usd is negative
        return self.daily_loss_usd > -self.daily_loss_cap_usd

    def reset_daily(self) -> None:
        """Reset daily counters — called at midnight by the agent loop."""
        self.daily_loss_usd = 0.0

    def is_halted(self) -> bool:
        """Check if trading should be halted due to drawdown breach."""
        return self.current_drawdown >= self.max_drawdown_pct

    def get_risk_metrics(self) -> dict:
        """Return current risk metrics."""
        return {
            "peak_value": round(self.peak_value, 2),
            "current_drawdown": round(self.current_drawdown, 4),
            "max_drawdown_pct": self.max_drawdown_pct,
            "max_position_pct": self.max_position_pct,
            "kelly_fraction": self.kelly_fraction,
            "daily_loss_usd": round(self.daily_loss_usd, 2),
            "daily_loss_cap_usd": self.daily_loss_cap_usd,
            "is_halted": self.is_halted(),
        }
