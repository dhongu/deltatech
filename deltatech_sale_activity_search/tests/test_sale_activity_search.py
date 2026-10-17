from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleActivitySearch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.order_a = cls.env["sale.order"].create({"partner_id": cls.partner.id})
        cls.order_b = cls.env["sale.order"].create({"partner_id": cls.partner.id})
        cls.type_call = cls.env["mail.activity.type"].create({"name": "Test Call"})
        cls.type_email = cls.env["mail.activity.type"].create({"name": "Test Email"})
        cls.sale_model = cls.env["ir.model"]._get("sale.order")
        cls.partner_model = cls.env["ir.model"]._get("res.partner")

    def _create_activity(self, record, model, activity_type):
        return self.env["mail.activity"].create(
            {
                "res_model_id": model.id,
                "res_id": record.id,
                "activity_type_id": activity_type.id,
                "user_id": self.env.user.id,
            }
        )

    def test_create_sets_activity_types(self):
        self._create_activity(self.order_a, self.sale_model, self.type_call)
        self.assertEqual(self.order_a.active_activity_types, "Test Call")

    def test_write_multiple_activities(self):
        activities = self._create_activity(self.order_a, self.sale_model, self.type_call)
        activities |= self._create_activity(self.order_b, self.sale_model, self.type_call)
        activities |= self._create_activity(self.partner, self.partner_model, self.type_call)
        activities.write({"activity_type_id": self.type_email.id})
        self.assertEqual(self.order_a.active_activity_types, "Test Email")
        self.assertEqual(self.order_b.active_activity_types, "Test Email")

    def test_move_activity_between_orders(self):
        activity = self._create_activity(self.order_a, self.sale_model, self.type_call)
        self.assertEqual(self.order_a.active_activity_types, "Test Call")
        activity.write({"res_id": self.order_b.id})
        self.assertFalse(self.order_a.active_activity_types)
        self.assertEqual(self.order_b.active_activity_types, "Test Call")

    def test_move_activity_to_other_model(self):
        activity = self._create_activity(self.order_a, self.sale_model, self.type_call)
        activity.write({"res_model_id": self.partner_model.id, "res_id": self.partner.id})
        self.assertFalse(self.order_a.active_activity_types)
