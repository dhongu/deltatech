from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleActivitySearch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Activity Search Partner"})
        cls.order = cls.env["sale.order"].create({"partner_id": cls.partner.id})
        cls.order2 = cls.env["sale.order"].create({"partner_id": cls.partner.id})
        cls.type_call = cls.env["mail.activity.type"].create({"name": "TB Call", "res_model": False})
        cls.type_email = cls.env["mail.activity.type"].create({"name": "TB Email", "res_model": False})

    def _schedule(self, order, activity_type):
        return order.activity_schedule(activity_type_id=activity_type.id, user_id=self.env.user.id)

    def _types(self, order):
        return set(filter(None, (order.active_activity_types or "").split(", ")))

    def test_create_and_unlink(self):
        call = self._schedule(self.order, self.type_call)
        self.assertEqual(self._types(self.order), {"TB Call"})
        self._schedule(self.order, self.type_email)
        self.assertEqual(self._types(self.order), {"TB Call", "TB Email"})
        self.assertFalse(self.order2.active_activity_types)
        call.unlink()
        self.assertEqual(self._types(self.order), {"TB Email"})

    def test_write_type_and_mark_done(self):
        call = self._schedule(self.order, self.type_call)
        call.activity_type_id = self.type_email
        self.assertEqual(self._types(self.order), {"TB Email"})
        email2 = self._schedule(self.order2, self.type_email)
        # marking several activities done at once archives them (multi-record write)
        (call | email2).action_feedback(feedback="done")
        self.assertFalse(self.order.active_activity_types)
        self.assertFalse(self.order2.active_activity_types)

    def test_search_by_activity_type(self):
        self._schedule(self.order, self.type_call)
        self._schedule(self.order2, self.type_email)
        found = self.env["sale.order"].search([("active_activity_types", "ilike", "TB Call")])
        self.assertIn(self.order, found)
        self.assertNotIn(self.order2, found)
