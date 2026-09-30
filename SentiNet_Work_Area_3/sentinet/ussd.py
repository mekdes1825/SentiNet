"""Local-only USSD-style mobile-money simulation using fictional data."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from uuid import uuid4
from typing import Any

class SimulationError(ValueError):
    pass

@dataclass
class Account:
    user_id: str
    phone_number: str
    pin: str
    balance: Decimal
    account_id: str
    locked: bool = False

@dataclass
class Event:
    event_id: str
    event_type: str
    timestamp: str
    user_id: str
    account_id: str
    phone_number: str
    session_id: str
    outcome: str
    details: dict[str, Any]
    def to_dict(self):
        data=asdict(self)
        data["details"] = dict(self.details)
        return data

class MobileMoneySimulator:
    """A toy menu backend; PINs are demo-only and never emitted in events."""
    def __init__(self, account: Account):
        if account.balance < 0: raise SimulationError("Initial balance cannot be negative")
        self.account=account
        self.events=[]
        self.session_id=str(uuid4())
        self.authenticated=False
        self.failed_attempts=0

    def _log(self, event_type, outcome, details=None):
        e=Event(str(uuid4()),event_type,datetime.now(timezone.utc).isoformat(),
                self.account.user_id,self.account.account_id,self.account.phone_number,
                self.session_id,outcome,details or {})
        self.events.append(e); return e

    def authenticate(self, pin: str):
        if self.account.locked:
            self.authenticated=False
            return self._log("auth.attempt","blocked",{"reason":"account_locked"})
        if pin == self.account.pin:
            self.authenticated=True; self.failed_attempts=0
            return self._log("auth.success","success",{})
        self.failed_attempts += 1
        if self.failed_attempts >= 3: self.account.locked=True
        return self._log("auth.failure","failure",{"attempt":self.failed_attempts,"locked":self.account.locked})

    def _require_auth(self):
        if not self.authenticated: raise SimulationError("Authenticate before using this menu action")
        if self.account.locked: raise SimulationError("Account is locked")

    def balance(self):
        self._require_auth()
        self._log("account.balance_viewed","success",{})
        return self.account.balance

    def transfer(self, amount, recipient_id="ACC-RECIPIENT-DEMO"):
        self._require_auth()
        try: value=Decimal(str(amount))
        except (InvalidOperation, ValueError): raise SimulationError("Amount must be numeric")
        if not value.is_finite() or value <= 0: raise SimulationError("Amount must be positive")
        if value > self.account.balance: 
            self._log("transaction.transfer","rejected",{"reason":"insufficient_virtual_funds","amount":str(value)})
            raise SimulationError("Insufficient virtual balance")
        self.account.balance -= value
        return self._log("transaction.transfer","success",{"amount":str(value),"currency":"SIM-ETB","recipient_id":recipient_id,"virtual_only":True})

    def change_pin(self, old_pin, new_pin):
        self._require_auth()
        if old_pin != self.account.pin:
            self._log("pin.change","failure",{"reason":"current_pin_mismatch"})
            raise SimulationError("Current demo PIN does not match")
        if not new_pin.isdigit() or len(new_pin) != 4: raise SimulationError("New demo PIN must be exactly 4 digits")
        self.account.pin=new_pin
        return self._log("pin.change","success",{"credential_stored": "in_memory_only"})

    def reset_pin(self, new_pin, simulated_approval=False):
        # Represents a controlled reset event; no OTP or real identity verification.
        if not simulated_approval: raise SimulationError("Pass simulated_approval=True for the demo reset")
        if not new_pin.isdigit() or len(new_pin) != 4: raise SimulationError("New demo PIN must be exactly 4 digits")
        self.account.pin=new_pin; self.authenticated=False
        return self._log("pin.reset","success",{"method":"fictional_demo_approval","requires_reauthentication":True})

    def menu(self):
        return ["1. Check virtual balance","2. Transfer virtual funds","3. Change demo PIN","4. Reset demo PIN","0. Exit"]

    def snapshot(self):
        return {"user_id":self.account.user_id,"account_id":self.account.account_id,
                "phone_number":self.account.phone_number,"virtual_balance":str(self.account.balance),
                "currency":"SIM-ETB","locked":self.account.locked,"authenticated":self.authenticated}
