# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _tb_set_invoice_company(self, name, vat, address=None):
        """Invoices the order to a company, given by name and VAT number.

        A company already recorded with this VAT number becomes the invoice address and the
        customer stays as it is: typing a VAT number on the website does not attach a visitor
        to the company, so they do not get to see its documents in the portal. Otherwise the
        company is created with its registered office and the customer becomes one of its
        delivery addresses, keeping its own address.

        :param dict address: the registered office, as `res.partner` values (state_id, city,
                             street, zip); the country is Romania.
        :return: the company partner, sudoed
        """
        self.ensure_one()
        Partner = self.env["res.partner"].sudo()
        vat = Partner._tb_clean_company_vat(vat)
        company = Partner._tb_find_company_by_vat(vat, self.company_id)
        customer = self.partner_id.sudo()
        if not company:
            values = {
                "name": name,
                "vat": vat,
                "country_id": self.env.ref("base.ro").id,
                "email": customer.email,
                "phone": customer.phone,
                "lang": customer.lang,
            }
            values.update(address or {})
            company = Partner.create(values)
            if not customer.is_company and not customer.parent_id:
                # As a delivery address the customer keeps its own address: a plain contact
                # would take the address of the company (the registered office).
                customer.write({"parent_id": company.id, "type": "delivery"})
        self.sudo().partner_invoice_id = company
        return company
