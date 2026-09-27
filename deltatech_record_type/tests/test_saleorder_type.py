# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestRecordType(TransactionCase):
    def setUp(self):
        super().setUp()
        # Ensure at least one partner exists for many2one tests
        self.partner = self.env["res.partner"].search([], limit=1)
        if not self.partner:
            self.partner = self.env["res.partner"].create({"name": "Test Partner"})

        # Create a Record Type for sale.order model
        self.rec_type = self.env["record.type"].create(
            {
                "name": "Sales Type",
                "model": "sale.order",
            }
        )

        # Prepare field records from ir.model.fields
        field_obj = self.env["ir.model.fields"].sudo()
        self.field_partner = field_obj.search([("model", "=", "sale.order"), ("name", "=", "partner_id")], limit=1)
        self.field_origin = field_obj.search([("model", "=", "sale.order"), ("name", "=", "origin")], limit=1)
        self.field_state = field_obj.search([("model", "=", "sale.order"), ("name", "=", "state")], limit=1)

    def test_compute_model_id_sets_model(self):
        line = self.env["record.type.default.values"].create(
            {
                "record_type_id": self.rec_type.id,
                "field_id": self.field_partner.id,
                "field_name": "",
                "field_value": "",
                "field_type": "char",
            }
        )
        # On create, computed field should set model_id to sale.order model
        self.assertEqual(line.model_id.model, "sale.order")

    def test_onchange_field_id_sets_types_and_names(self):
        # Many2one: field_type -> 'id'
        line = self.env["record.type.default.values"].new(
            {
                "record_type_id": self.rec_type.id,
                "field_id": self.field_partner.id,
            }
        )
        line._onchange_field_id()
        self.assertEqual(line.field_type, "id")
        self.assertTrue(line.field_name)
        self.assertEqual(line.field_name, self.field_partner.name)

        # Char: field_type -> 'char'
        if self.field_origin:
            line = self.env["record.type.default.values"].new(
                {
                    "record_type_id": self.rec_type.id,
                    "field_id": self.field_origin.id,
                }
            )
            line._onchange_field_id()
            self.assertEqual(line.field_type, "char")

        # Selection: field_type -> 'char'
        if self.field_state:
            line = self.env["record.type.default.values"].new(
                {
                    "record_type_id": self.rec_type.id,
                    "field_id": self.field_state.id,
                }
            )
            line._onchange_field_id()
            self.assertEqual(line.field_type, "char")

    def test_compute_and_inverse_resource_ref(self):
        # Create line with many2one field; no field_value set initially
        line = self.env["record.type.default.values"].create(
            {
                "record_type_id": self.rec_type.id,
                "field_id": self.field_partner.id,
                "field_name": self.field_partner.name,
                "field_value": "",  # trigger auto-pick in compute
                "field_type": "id",
            }
        )
        # compute method should have populated value_ref and possibly field_value
        self.assertTrue(line.value_ref or line.field_value)
        # If value_ref computed, it should reference res.partner model
        if line.value_ref:
            self.assertEqual(line.value_ref._name, "res.partner")

        # Now set value_ref explicitly and test inverse sets field_value id
        line.value_ref = self.partner
        line._inverse_resource_ref()
        self.assertEqual(int(line.field_value or 0), self.partner.id)

    def test_selection_target_model_contains_sale_order(self):
        # Call selection method and verify sale.order appears
        selection = self.env["record.type.default.values"]._selection_target_model()
        models = [key for key, _label in selection]
        self.assertIn("sale.order", models)
