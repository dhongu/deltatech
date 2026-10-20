# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged

from odoo.addons.website_sale import const


@tagged("post_install", "-at_install")
class TestWebsiteTaxDisplaySticky(TransactionCase):
    @staticmethod
    def _standard_default(website):
        # Odoo 20: the default depends on the fiscal country (tax excluded only in CA/US)
        country_code = website.company_id.account_fiscal_country_id.code
        return "tax_excluded" if country_code in const.TAX_EXCLUDED_COUNTRIES else "tax_included"

    def test_company_address_write_does_not_reset_tax_display(self):
        website = self.env["website"].search([], limit=1)
        # the value the standard recompute would NOT give back
        chosen = "tax_included" if self._standard_default(website) == "tax_excluded" else "tax_excluded"
        website.write({"show_line_subtotals_tax_selection": chosen})
        self.assertEqual(website.show_line_subtotals_tax_selection, chosen)

        partner = website.company_id.partner_id
        partner.write({"street": (partner.street or "") + " TEST"})
        website.invalidate_recordset(["show_line_subtotals_tax_selection"])

        self.assertEqual(
            website.show_line_subtotals_tax_selection,
            chosen,
            "Scrierea adresei partenerului companiei nu trebuie sa reseteze "
            "silentios setarea de afisare a preturilor pe website.",
        )

    def test_new_website_keeps_default(self):
        website = self.env["website"].create({"name": "Test website sticky default"})
        self.assertEqual(website.show_line_subtotals_tax_selection, self._standard_default(website))
