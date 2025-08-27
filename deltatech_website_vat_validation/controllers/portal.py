# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalVATValidation(CustomerPortal):
    def details_form_validate(self, data, partner_creation=False):
        if data.get("vat"):
            data["vat"] = data.get("vat").strip()

        error, error_message = super().details_form_validate(data, partner_creation)

        vat = data.get("vat", False)
        if vat and "vat" not in error:
            partner = request.env["res.users"].browse(request.uid).partner_id
            domain = [("vat", "=", vat), ("id", "!=", partner.id), ("parent_id", "=", False)]
            partner_vat = request.env["res.partner"].sudo().search(domain, limit=1)
            if partner_vat:
                error["vat"] = "error"
                error_message.append("VAT already exist")
            else:
                # preluare nume din ANAF
                pass

        return error, error_message
