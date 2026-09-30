import unittest
from decimal import Decimal
from sentinet.ussd import Account,MobileMoneySimulator,SimulationError

class UssdTests(unittest.TestCase):
 def setUp(self): self.app=MobileMoneySimulator(Account("USR-T","+251-900-000-000","1234",Decimal("100"),"ACC-T"))
 def test_auth_and_balance(self):
  self.app.authenticate("1234"); self.assertEqual(self.app.balance(),Decimal("100"))
 def test_three_failures_lock(self):
  for _ in range(3): self.app.authenticate("0000")
  self.assertTrue(self.app.account.locked)
 def test_transfer_updates_virtual_balance(self):
  self.app.authenticate("1234"); self.app.transfer("25")
  self.assertEqual(self.app.account.balance,Decimal("75"))
 def test_unauthenticated_transfer_rejected(self):
  with self.assertRaises(SimulationError): self.app.transfer("1")
 def test_pin_reset_requires_demo_approval(self):
  with self.assertRaises(SimulationError): self.app.reset_pin("5678")
  self.app.reset_pin("5678",simulated_approval=True)
  self.assertFalse(self.app.authenticated)
 def test_events_never_include_pin(self):
  self.app.authenticate("1234")
  self.assertNotIn("1234",str([e.to_dict() for e in self.app.events]))
if __name__=="__main__": unittest.main()
