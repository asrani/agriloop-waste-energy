import copy
import unittest
from model import initial_state, deposit, process, trade, verify, STREAMS, PARTICIPANTS

class ModelTests(unittest.TestCase):
    def setUp(self): self.state = initial_state()
    def test_seed_and_hash_tampering(self):
        self.assertTrue(verify(self.state['ledger']))
        self.state['ledger'][0]['payload']['mass_kg'] += 1
        self.assertFalse(verify(self.state['ledger']))
    def test_rewards_and_duplicate_prevention(self):
        batch = deposit(self.state, PARTICIPANTS[0], STREAMS[0], 100, 90)
        old = self.state['wallets'][PARTICIPANTS[0]].copy()
        process(self.state, batch, 30, 8, 90)
        self.assertAlmostEqual(self.state['wallets'][PARTICIPANTS[0]]['R'] - old['R'], 27)
        self.assertEqual(self.state['wallets'][PARTICIPANTS[0]]['E'] - old['E'], 8)
        snapshot = copy.deepcopy(self.state)
        with self.assertRaises(ValueError): process(self.state, batch, 30, 8, 90)
        self.assertEqual(self.state, snapshot)
    def test_trade_conserves_balances(self):
        e = sum(v['E'] for v in self.state['wallets'].values())
        cash = sum(v['cash'] for v in self.state['wallets'].values())
        trade(self.state, PARTICIPANTS[0], PARTICIPANTS[3], 5, .3)
        self.assertAlmostEqual(sum(v['E'] for v in self.state['wallets'].values()), e)
        self.assertAlmostEqual(sum(v['cash'] for v in self.state['wallets'].values()), cash)
        self.assertTrue(verify(self.state['ledger']))
    def test_invalid_trade_is_atomic(self):
        for seller,buyer,qty,price in [(0,3,9999,.3),(0,3,1,1000),(0,0,1,.3),(0,3,float('nan'),.3)]:
            snapshot = copy.deepcopy(self.state)
            with self.assertRaises(ValueError): trade(self.state,PARTICIPANTS[seller],PARTICIPANTS[buyer],qty,price)
            self.assertEqual(self.state, snapshot)
    def test_mass_and_ewaste_validation(self):
        batch = deposit(self.state,PARTICIPANTS[2],STREAMS[2],10,80)
        for recovered,energy in [(11,0),(5,2)]:
            snapshot=copy.deepcopy(self.state)
            with self.assertRaises(ValueError):process(self.state,batch,recovered,energy,90)
            self.assertEqual(self.state,snapshot)

if __name__ == '__main__': unittest.main()
