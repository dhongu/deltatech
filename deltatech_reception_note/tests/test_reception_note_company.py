# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestReceptionNoteCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Reception Note Company B"})
        cls.env.user.company_ids |= cls.company_b
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=[cls.company_a.id, cls.company_b.id]))
        cls.partner = cls.env["res.partner"].create({"name": "Reception Note Vendor"})
        cls.product = cls.env["product.product"].create(
            {"name": "Reception Note Product", "default_code": "RN-MC", "is_storable": True}
        )

    def _order(self, company, qty, reception_type="normal", **values):
        order = (
            self.env["purchase.order"]
            .with_company(company)
            .create(
                {
                    "partner_id": self.partner.id,
                    "company_id": company.id,
                    "reception_type": reception_type,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product.id,
                                "name": self.product.name,
                                "product_qty": qty,
                                "uom_id": self.product.uom_id.id,
                                "price_unit": 100,
                            },
                        )
                    ],
                    **values,
                }
            )
        )
        return order

    def test_reception_note_consumes_only_own_company_rfq(self):
        """RECEPTION-002: an older sent RFQ of another allowed company must stay untouched."""
        rfq_b = self._order(
            self.company_b, 10, "rfq_only", date_order=fields.Datetime.subtract(fields.Datetime.now(), days=10)
        )
        rfq_b.state = "sent"
        rfq_a = self._order(self.company_a, 10, "rfq_only")
        rfq_a.state = "sent"

        note = self._order(self.company_a, 4, "note")
        note.button_confirm()

        self.assertEqual(rfq_b.order_line.product_qty, 10)
        self.assertFalse(rfq_b.is_empty)
        self.assertEqual(rfq_a.order_line.product_qty, 6)

    def test_create_reception_note_keeps_source_company_and_currency(self):
        """RECEPTION-004: the RFQ-only counterpart keeps the company and currency of its prices."""
        eur = self.env.ref("base.EUR")
        eur.active = True
        usd = self.env.ref("base.USD")
        usd.active = True
        currency = eur if self.company_b.currency_id != eur else usd
        source = self._order(self.company_b, 10, currency_id=currency.id)
        self.assertEqual(source.currency_id, currency)
        # the wizard runs while company A is the active company
        self.assertEqual(self.env.company, self.company_a)
        existing = self.env["purchase.order"].search([("reception_type", "=", "rfq_only")])

        self.env["reception.note.create"].create({}).with_context(active_ids=source.ids).do_create_reception_note()

        rfq = self.env["purchase.order"].search([("reception_type", "=", "rfq_only")]) - existing
        self.assertEqual(len(rfq), 1)
        self.assertRecordValues(
            rfq,
            [
                {
                    "company_id": self.company_b.id,
                    "currency_id": currency.id,
                    "picking_type_id": source.picking_type_id.id,
                    "state": "sent",
                }
            ],
        )
        self.assertRecordValues(rfq.order_line, [{"product_qty": 10, "price_unit": 100}])
