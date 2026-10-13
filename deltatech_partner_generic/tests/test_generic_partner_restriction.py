from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGenericPartnerRestriction(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.generic_partner = cls.env["res.partner"].create({"name": "Generic customer"})
        cls.regular_partner = cls.env["res.partner"].create({"name": "Regular customer"})
        cls.env.company.generic_partner_id = cls.generic_partner
        cls.restricted_journal = cls.env["account.journal"].search(
            [
                ("company_id", "=", cls.env.company.id),
                ("type", "in", ("bank", "cash")),
                ("inbound_payment_method_line_ids", "!=", False),
            ],
            limit=1,
        )
        cls.restricted_journal.restriction = True

    def _new_payment(self, partner):
        return self.env["account.payment"].new(
            {
                "company_id": self.env.company.id,
                "partner_id": partner.id,
                "payment_type": "inbound",
                "partner_type": "customer",
            }
        )

    def test_restricted_journal_is_hidden_for_generic_partner(self):
        payment = self._new_payment(self.generic_partner)

        self.assertNotIn(self.restricted_journal, payment.available_journal_ids._origin)

    def test_restricted_journal_is_available_for_regular_partner(self):
        payment = self._new_payment(self.regular_partner)

        self.assertIn(self.restricted_journal, payment.available_journal_ids._origin)
