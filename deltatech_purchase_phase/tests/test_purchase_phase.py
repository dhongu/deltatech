# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestPurchasePhase(TransactionCase):
    def setUp(self):
        super().setUp()
        self.PurchaseOrder = self.env["purchase.order"]
        self.PurchaseOrderPhase = self.env["purchase.order.phase"]
        self.Partner = self.env["res.partner"]

        # Minimal vendor to create a purchase order
        self.vendor = self.Partner.create(
            {
                "name": "Vendor Test",
                "supplier_rank": 1,
            }
        )

        # Create a purchase order in draft
        self.po = self.PurchaseOrder.create(
            {
                "partner_id": self.vendor.id,
            }
        )

    def test_phase_created_and_set_on_state_sent(self):
        # Ensure no phase with code 'rfq' exists (data may load it, so just proceed)
        # Writing state to 'sent' should set phase to 'rfq'
        self.po.write({"state": "sent"})

        self.assertTrue(self.po.phase_id, "Phase should be set when state becomes 'sent'")
        self.assertEqual(self.po.phase_id.code, "rfq", "Phase code should be 'rfq' when PO state is 'sent'")

    def test_phase_set_on_state_purchase(self):
        # Move to purchase state should set phase to 'purchase_confirm'
        self.po.write({"state": "purchase"})

        self.assertTrue(self.po.phase_id, "Phase should be set when state becomes 'purchase'")
        self.assertEqual(
            self.po.phase_id.code,
            "purchase_confirm",
            "Phase code should be 'purchase_confirm' when PO state is 'purchase'",
        )

    def test_set_phase_creates_missing_code(self):
        code = "custom_code_xyz"
        existing = self.PurchaseOrderPhase.search([("code", "=", code)])
        self.assertFalse(existing, "Precondition failed: phase with custom code should not exist before test")

        # Call helper which should create phase if missing and set it
        self.po.set_phase(code)

        created = self.PurchaseOrderPhase.search([("code", "=", code)], limit=1)
        self.assertTrue(created, "set_phase must auto-create missing phase by code")
        self.assertEqual(created.name, code, "Auto-created phase name should default to the provided code")
        self.assertEqual(self.po.phase_id, created, "Purchase order's phase_id must be set to the created phase")
