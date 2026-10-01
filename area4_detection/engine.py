from typing import Any

from .rules import (
    DetectionAlert,
    detect_full_account_takeover_pattern,
    detect_sim_swap_followed_by_pin_reset,
    detect_sim_swap_followed_by_transfer,
)


class BehavioralDetectionEngine:
    """
    Area 4 behavioral detection engine.

    Receives events from the simulated SIM-Swap and
    Mobile-Money components and evaluates them against
    account-takeover detection rules.
    """

    def __init__(self, window_seconds: int = 300):
        if window_seconds <= 0:
            raise ValueError("window_seconds must be greater than zero")

        self.window_seconds = window_seconds

    def analyze(self, events: list[Any]) -> list[DetectionAlert]:
        """
        Analyze a collection of events and return all detected alerts.

        Events may be DetectionEvent objects or compatible dictionaries.
        """
        if not events:
            return []

        alerts: list[DetectionAlert] = []

        alerts.extend(
            detect_sim_swap_followed_by_pin_reset(
                events,
                window_seconds=self.window_seconds,
            )
        )

        alerts.extend(
            detect_sim_swap_followed_by_transfer(
                events,
                window_seconds=self.window_seconds,
            )
        )

        alerts.extend(
            detect_full_account_takeover_pattern(
                events,
                window_seconds=self.window_seconds,
            )
        )

        return self._remove_duplicate_alerts(alerts)

    @staticmethod
    def _remove_duplicate_alerts(
        alerts: list[DetectionAlert],
    ) -> list[DetectionAlert]:
        """
        Remove duplicate alerts while preserving their original order.
        """
        unique_alerts: list[DetectionAlert] = []
        seen: set[tuple[str, str, str]] = set()

        for alert in alerts:
            key = (
                alert.rule_id,
                alert.user_id,
                alert.timestamp,
            )

            if key not in seen:
                seen.add(key)
                unique_alerts.append(alert)

        return unique_alerts

    @staticmethod
    def highest_risk(alerts: list[DetectionAlert]) -> str:
        """
        Return the highest risk level among detected alerts.
        """
        if not alerts:
            return "LOW"

        priority = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "CRITICAL": 4,
        }

        return max(
            alerts,
            key=lambda alert: priority.get(alert.risk_level.upper(), 0),
        ).risk_level.upper()

    @staticmethod
    def summary(alerts: list[DetectionAlert]) -> dict[str, Any]:
        """
        Create a simple summary suitable for a future dashboard/API.
        """
        return {
            "alert_count": len(alerts),
            "highest_risk": BehavioralDetectionEngine.highest_risk(alerts),
            "alerts": [alert.to_dict() for alert in alerts],
        }