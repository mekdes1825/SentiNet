from dataclasses import dataclass
from enum import Enum


class SIMState(Enum):
    VICTIM_CONTROLLED = "victim_controlled"
    ATTACKER_CONTROLLED = "attacker_controlled"


class SIMSwapScenario(Enum):
    NORMAL = "normal"
    SUSPICIOUS = "suspicious"


@dataclass
class SimUser:
    user_id: str
    phone_number: str
    sim_state: SIMState = SIMState.VICTIM_CONTROLLED
