from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGenericPartnerRestriction(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.generic_partner = cls.env["res.partner"].create({"name": "Generic customer"})
        cls.regular_partner = cls.env["res.partner"].create({"name": "Regular customer"})
        cls.env.company.generic_partner_id = cls.generic_partner
        # the journal proposed by core on a new customer payment
        cls.restricted_journal = (
            cls.env["account.payment"]
            .new(
                {
                    "company_id": cls.env.company.id,
                    "partner_id": cls.regular_partner.id,
                    "payment_type": "inbound",
                    "partner_type": "customer",
                }
            )
            .journal_id._origin
        )
        cls.restricted_journal.restriction = True
        cls.allowed_journal = cls.env["account.journal"].create(
            {"name": "Generic cash", "code": "TGCSH", "type": "cash", "sequence": 99}
        )

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

    def test_default_journal_is_allowed_for_generic_partner(self):
        payment = self._new_payment(self.generic_partner)

        self.assertEqual(payment.journal_id._origin, self.allowed_journal)

    def test_default_journal_unchanged_for_regular_partner(self):
        payment = self._new_payment(self.regular_partner)

        self.assertEqual(payment.journal_id._origin, self.restricted_journal)
