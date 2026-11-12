# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models

# Fields of the registered office compared to reuse an invoice address already typed.
TB_OFFICE_FIELDS = ("name", "street", "zip", "city", "state_id")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _tb_prepare_invoice_company(self, name, vat, address=None):
        """The invoice address of a company, given by the name, the VAT number and the
        registered office typed on the website; the order is left as it is (the website
        sets it through `_update_address`).

        The invoice address always holds the name and the registered office typed by the
        visitor; of a company already recorded, only its name shows on the address (as its
        parent), the data recorded on it (address, contacts) do not.

        - No company recorded with this VAT number: the company is created with its
          registered office and the customer becomes one of its delivery addresses, keeping
          its own address.
        - A company already recorded with this VAT number: the invoice address with the same
          name and registered office under it is reused, or a new one is created, so the
          invoice goes to that company (its commercial partner). The customer is not attached
          to the company and does not get to see its documents in the portal.

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
            # The company itself (e.g. created by a previous order with the same data) or one
            # of its invoice addresses, when the name and the registered office match.
            domain = ["|", ("id", "=", company.id), "&", ("parent_id", "=", company.id), ("type", "=", "invoice")]
            domain += [(fname, "=", values.get(fname) or False) for fname in TB_OFFICE_FIELDS]
            invoice_address = Partner.search(domain, order="id", limit=1)
            if not invoice_address:
                invoice_address = Partner.create({**values, "parent_id": company.id, "type": "invoice"})
        else:
            invoice_address = Partner.create({**values, "vat": vat})
            if not customer.is_company and not customer.parent_id:
                # As a delivery address the customer keeps its own address: a plain contact
                # would take the address of the company (the registered office).
                customer.write({"parent_id": invoice_address.id, "type": "delivery"})
        return invoice_address
