# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _tb_set_invoice_company(self, name, vat, address=None):
        """Invoices the order to a company (see `_tb_prepare_invoice_company`); the taxes
        follow a change of fiscal position. On the website the cart is updated through
        `_update_address` instead, which also refreshes the session.

        :return: the invoice address, sudoed
        """
        self.ensure_one()
        invoice_address = self._tb_prepare_invoice_company(name, vat, address)
        fiscal_position = self.fiscal_position_id
        self.sudo().partner_invoice_id = invoice_address
        if self.fiscal_position_id != fiscal_position:
            self.sudo()._recompute_taxes()
        return invoice_address

    def _tb_prepare_invoice_company(self, name, vat, address=None):
        """The invoice address of a company, given by the name, the VAT number and the
        registered office typed on the website; the order is left as it is.

        The invoice address always holds the name and the registered office typed by the
        visitor; of a company already recorded, only its name shows on the address (as its
        parent), the data recorded on it (address, contacts) do not.

        - No company recorded with this VAT number: the company is created with its
          registered office and the customer becomes one of its delivery addresses, keeping
          its own address.
        - A company already recorded with this VAT number: a new invoice address is created
          under it, so the invoice goes to that company (its commercial partner). The
          customer is not attached to the company and does not get to see its documents in
          the portal.

        :param dict address: the registered office, as `res.partner` values (state_id, city,
                             street, zip); the country is Romania.
        :return: the invoice address, sudoed
        """
        self.ensure_one()
        Partner = self.env["res.partner"].sudo()
        vat = Partner._tb_clean_company_vat(vat)
        customer = self.partner_id.sudo()
        values = {
            "name": name,
            "country_id": self.env.ref("base.ro").id,
            "email": customer.email,
            "phone": customer.phone,
            "lang": customer.lang,
            **(address or {}),
        }
        company = Partner._tb_find_company_by_vat(vat, self.company_id)
        if company:
            invoice_address = Partner.create({**values, "parent_id": company.id, "type": "invoice"})
        else:
            invoice_address = Partner.create({**values, "vat": vat})
            if not customer.is_company and not customer.parent_id:
                # As a delivery address the customer keeps its own address: a plain contact
                # would take the address of the company (the registered office).
                customer.write({"parent_id": invoice_address.id, "type": "delivery"})
        return invoice_address
