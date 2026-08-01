import unittest
from pathlib import Path

class StateMachineContract(unittest.TestCase):
    def test_required_states_and_safe_defaults(self):
        h=Path(__file__).parents[1]/'src/controller.h'; s=h.read_text()
        for name in ('OFF','ARMING','SOFT_START','RUN','OVERCURRENT','UNDERVOLTAGE','OVERTEMPERATURE','FAULT_LATCHED'):
            self.assertIn(name,s)
        self.assertIn('float duty=0',s)
    def test_configured_targets(self):
        s=(Path(__file__).parents[1]/'src/config.h').read_text()
        self.assertIn('15.0f',s); self.assertIn('16.5f',s); self.assertIn('90.0f',s); self.assertIn('20000.0f',s)
if __name__=='__main__': unittest.main()
