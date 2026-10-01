from collections import deque
from typing import Any

from .engine import BehavioralDetectionEngine
from .events import DetectionEvent
from .rules import DetectionAlert


class RealTimeMonitor:
    """
    Maintains a recent event buffer and checks new events
    against the behavioral detection rules.
    """

    def __init__(
        self,
        window_seconds: int = 300,
        max_events: int = 1000,
    ):
        if window_seconds <= 0:
            raise ValueError("window_seconds must be greater than zero")

        if max_events <= 0:
            raise ValueError("max_events must be greater than zero")

        self.window_seconds = window_seconds
        self.max_events = max_events

        self.engine = BehavioralDetectionEngine(
            window_seconds=window_seconds
        )

        self.events = deque(maxlen=max_events)
        self.alerts: list[DetectionAlert] = []

    def add_event(self, event: DetectionEvent) -> list[DetectionAlert]:
        """
        Add one event and immediately check the recent event history.

        Returns only alerts that were not already stored by the monitor.
        """
        if not isinstance(event, DetectionEvent):
            raise TypeError("event must be a DetectionEvent")

        self.events.append(event)

        current_events = list(self.events)
        detected_alerts = self.engine.analyze(current_events)

        existing_keys = {
            (
                alert.rule_id,
                alert.user_id,
                tuple(alert.matched_events),
            )
            for alert in self.alerts
        }

        new_alerts: list[DetectionAlert] = []

        for alert in detected_alerts:
            alert_key = (
                alert.rule_id,
                alert.user_id,
                tuple(alert.matched_events),
            )

            if alert_key not in existing_keys:
                self.alerts.append(alert)
                new_alerts.append(alert)
                existing_keys.add(alert_key)

        return new_alerts

    def get_recent_events(self) -> list[DetectionEvent]:
        """Return the events currently stored in the monitoring buffer."""
        return list(self.events)

    def get_alerts(self) -> list[DetectionAlert]:
        """Return all alerts currently known to the monitor."""
        return list(self.alerts)

    def latest_alert(self) -> DetectionAlert | None:
        """Return the most recent alert, if one exists."""
        if not self.alerts:
            return None

        return self.alerts[-1]

    def summary(self) -> dict[str, Any]:
        """Return a simple monitoring summary."""
        return {
            "event_count": len(self.events),
            "alert_count": len(self.alerts),
            "highest_risk": self.engine.highest_risk(self.alerts),
            "alerts": [
                alert.to_dict()
                for alert in self.alerts
            ],
        }