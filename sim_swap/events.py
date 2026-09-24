from dataclasses import dataclass
from datetime import datetime


@dataclass
class SIMSwapEvent:
    event_type: str
    user_id: str
    phone_number: str
    old_state: str
    new_state: str
    scenario: str
    timestamp: str

    @classmethod
    def create(
        cls,
        user_id: str,
        phone_number: str,
        old_state: str,
        new_state: str,
        scenario: str,
    ):
        return cls(
            event_type="SIM_REREGISTRATION",
            user_id=user_id,
            phone_number=phone_number,
            old_state=old_state,
            new_state=new_state,
            scenario=scenario,
            timestamp=datetime.now().isoformat(),
        )

    def to_dict(self):
        return {
            "event_type": self.event_type,
            "user_id": self.user_id,
            "phone_number": self.phone_number,
            "old_state": self.old_state,
            "new_state": self.new_state,
            "scenario": self.scenario,
            "timestamp": self.timestamp,
        }
