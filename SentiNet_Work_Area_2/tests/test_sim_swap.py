import unittest
from datetime import datetime, timezone
from sentinet.sim_swap import SimRecord, SimSwapSimulator, SimulationError

class SimSwapTests(unittest.TestCase):
    def setUp(self):
        self.sim = SimSwapSimulator(SimRecord("USR-TEST", "+251-900-000-000", "SIM-TEST"))

    def test_normal_reregistration_preserves_control(self):
        e = self.sim.reregister(actor="user", suspicious=False,
                                timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(self.sim.record.state, "victim_controlled")
        self.assertFalse(e.details["control_changed"])

    def test_suspicious_transition(self):
        e = self.sim.reregister(actor="unknown_actor", suspicious=True)
        self.assertEqual(self.sim.record.state, "attacker_controlled")
        self.assertEqual(e.previous_state, "victim_controlled")
        self.assertEqual(e.new_state, "attacker_controlled")

    def test_empty_actor_rejected(self):
        with self.assertRaises(SimulationError):
            self.sim.reregister(actor=" ")

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(SimulationError):
            self.sim.reregister(actor="user", timestamp=datetime(2026, 1, 1))

if __name__ == "__main__":
    unittest.main()
