import unittest
from planner import allocate, validate_jobs, validate_rates, price_load

class PlannerTests(unittest.TestCase):
    def job(self,ident='A',kg=3,cbm=4):
        return dict(job_id=ident,weight_kg=kg,volume_m3=cbm,priority=1)
    def rate(self,**kw):
        r=dict(min_kg=0,max_kg=100,min_m3=0,max_m3=100,amount=100,currency='INR',basis='per trip',origin='Delhi',destination='Mumbai',valid_from='2026-01-01',valid_until='2026-12-31',source='synthetic test quote',included_charges='test only')
        return dict(r,**kw)
    def test_allocate_all_once_and_unpriced(self):
        jobs=[self.job(str(i),6,4) for i in range(4)]
        r=allocate(jobs,10,10)
        self.assertEqual(len(r['loads']),4)
        self.assertEqual(len({j['job_id'] for l in r['loads'] for j in l['jobs']}),4)
        self.assertTrue(all(l['price']['amount'] is None for l in r['loads']))
    def test_oversize_not_lost(self):
        r=allocate([self.job('ok'),self.job('large',11)],10,10)
        self.assertEqual(r['unassigned'][0]['job_id'],'large')
        self.assertEqual(len(r['loads']),1)
    def test_capacity_and_boundary(self):
        r=allocate([self.job('a',10,10)],10,10)
        self.assertEqual(r['loads'][0]['weight_kg'],10)
    def test_price_does_not_change_allocation(self):
        a=allocate([self.job()],10,10)
        b=allocate([self.job()],10,10,[self.rate()], '2026-11-17','Delhi','Mumbai')
        self.assertEqual(a['loads'][0]['jobs'],b['loads'][0]['jobs'])
        self.assertEqual(b['loads'][0]['price']['amount'],100)
    def test_invalid_inputs(self):
        for v in [float('nan'),float('inf'),1e308,-1,0,'text']:
            with self.assertRaises(ValueError): validate_jobs([self.job(kg=v)])
        with self.assertRaises(ValueError): validate_jobs([self.job(),self.job()])
        with self.assertRaises(ValueError): validate_jobs([])
        with self.assertRaises(ValueError): allocate([self.job()],0,10)
    def test_rates(self):
        r=validate_rates([self.rate()])
        def p(rs=r,day='2026-11-17',origin='Delhi'):
            return price_load(10,10,rs,day,origin,'Mumbai')
        self.assertEqual(p()['amount'],100)
        self.assertIsNone(p(day='2027-01-01')['amount'])
        self.assertIsNone(p(origin='Chennai')['amount'])
        self.assertEqual(p(r+r)['status'],'ambiguous rates')
        self.assertEqual(p(validate_rates([self.rate(amount=0)]))['amount'],0)
        self.assertEqual(p(validate_rates([self.rate(basis='per tonne')]))['amount'],1)
        self.assertEqual(p(validate_rates([self.rate(basis='per m³')]))['amount'],1000)
        for bad in [dict(amount=-1),dict(valid_until='bad'),dict(max_kg=-1),dict(source='')]:
            with self.assertRaises(ValueError): validate_rates([self.rate(**bad)])
    def test_rate_normalization_and_overflow(self):
        r=validate_rates([self.rate(valid_from='20260101',valid_until='20261231',origin=123)])
        self.assertEqual(r[0]['valid_from'],'2026-01-01')
        self.assertEqual(r[0]['origin'],'123')
        self.assertEqual(price_load(10,10,r,'2026-11-17','123','Mumbai')['amount'],100)
        with self.assertRaises(ValueError):validate_rates([self.rate(amount=1e308)])
    def test_repeated_runs_independent(self):
        jobs=[self.job()]; rates=[self.rate()]
        a=allocate(jobs,10,10,rates); b=allocate(jobs,10,10,rates)
        self.assertEqual(a,b); self.assertEqual(len(jobs),1)

if __name__=='__main__':unittest.main()
