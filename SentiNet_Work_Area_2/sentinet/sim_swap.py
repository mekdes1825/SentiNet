"""Fictional SIM re-registration simulator; no network or telecom integration."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any


class SimulationError(ValueError):
    """Raised when a requested state transition is invalid."""


@dataclass
class SimRecord:
    user_id: str
    phone_number: str
    sim_id: str
    state: str = "victim_controlled"


@dataclass
class SimEvent:
    event_id: str
    event_type: str
    timestamp: str
    user_id: str
    phone_number: str
    sim_id: str
    previous_state: str
    new_state: str
    actor: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SimSwapSimulator:
    """Stateful simulator with an append-only in-memory event log."""
    VALID_STATES = {"victim_controlled", "attacker_controlled"}

    def __init__(self, record: SimRecord):
        if record.state not in self.VALID_STATES:
            raise SimulationError(f"Unsupported initial state: {record.state}")
        self.record = record
        self.events: list[SimEvent] = []

    def reregister(self, *, actor: str, suspicious: bool = False,
                    timestamp: datetime | None = None) -> SimEvent:
        if not actor.strip():
            raise SimulationError("actor must be a non-empty label")
        old = self.record.state
        if old != "victim_controlled":
            raise SimulationError(f"Cannot re-register from state {old}")
        new = "attacker_controlled" if suspicious else "victim_controlled"
        # A legitimate re-registration replaces a SIM but preserves account control.
        if suspicious:
            self.record.state = new
        stamp = timestamp or datetime.now(timezone.utc)
        if stamp.tzinfo is None:
            raise SimulationError("timestamp must include timezone information")
        event = SimEvent(
            event_id=str(uuid4()), event_type="sim.reregistration",
            timestamp=stamp.astimezone(timezone.utc).isoformat(),
            user_id=self.record.user_id, phone_number=self.record.phone_number,
            sim_id=self.record.sim_id, previous_state=old, new_state=new,
            actor=actor,
            details={"scenario": "suspicious" if suspicious else "normal",
                     "control_changed": suspicious,
                     "environment": "fictional_simulation"},
        )
        self.events.append(event)
        return event

    def snapshot(self) -> dict[str, Any]:
        return {"user_id": self.record.user_id, "phone_number": self.record.phone_number,
                "sim_id": self.record.sim_id, "state": self.record.state}
