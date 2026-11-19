from odoo.modules.neutralize import get_neutralization_queries
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTcNeutralize(TransactionCase):
    def test_neutralize_regenerates_keys_and_closes_queue(self):
        Station = self.env["deltatech.tc.station"]
        stations = Station.create([{"name": "Prod A"}, {"name": "Prod B"}])
        old_keys = set(stations.mapped("api_key"))
        Job = self.env["deltatech.tc.job"]
        pending = Job.create({"station_id": stations[0].id, "job_type": "ping"})
        done = Job.create({"station_id": stations[0].id, "job_type": "ping", "state": "done"})

        self.env.flush_all()
        for query in get_neutralization_queries(["deltatech_tc"]):
            self.env.cr.execute(query)
        self.env.invalidate_all()

        new_keys = stations.mapped("api_key")
        self.assertEqual(len(set(new_keys)), 2, "each station gets its own key")
        self.assertFalse(old_keys & set(new_keys), "no production key survives")
        self.assertTrue(all(len(k) == 64 for k in new_keys))
        self.assertFalse(Station._authenticate(next(iter(old_keys))))
        self.assertEqual(Station._authenticate(new_keys[0]), stations[0])
        self.assertEqual(pending.state, "error")
        self.assertIn("neutralized", pending.error)
        self.assertEqual(done.state, "done", "finished jobs are kept as they are")
