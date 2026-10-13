# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWebsiteTaxDisplaySticky(TransactionCase):
    def test_company_address_write_does_not_reset_tax_display(self):
        website = self.env["website"].search([], limit=1)
        website.write({"show_line_subtotals_tax_selection": "tax_included"})
        self.assertEqual(website.show_line_subtotals_tax_selection, "tax_included")

        partner = website.company_id.partner_id
        partner.write({"street": (partner.street or "") + " TEST"})
        website.invalidate_recordset(["show_line_subtotals_tax_selection"])

        self.assertEqual(
            website.show_line_subtotals_tax_selection,
            "tax_included",
            "Scrierea adresei partenerului companiei nu trebuie sa reseteze "
            "silentios setarea de afisare a preturilor pe website.",
        )

    def test_new_website_keeps_default(self):
        website = self.env["website"].create({"name": "Test website sticky default"})
        self.assertEqual(website.show_line_subtotals_tax_selection, "tax_excluded")
