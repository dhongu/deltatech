# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.http import request

from odoo.addons.phone_validation.tools import phone_validation
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleVATValidation(WebsiteSale):
    def checkout_form_validate(self, mode, all_form_values, data):
        error = dict()
        error_message = []

        if data.get("vat"):
            data["vat"] = data.get("vat").strip()

        standard_error, standard_error_message = super().checkout_form_validate(mode, all_form_values, data)

        error.update(standard_error)
        error_message += standard_error_message
        vat = data.get("vat", False)
        if vat and 'vat' not in error:
            partner = request.env['res.users'].browse(request.uid).partner_id
            domain = [("vat", "=", vat),('id','!=',partner.id),('parent_id','=',False)]
            partner_vat = request.env['res.partner'].search(domain, limit=1)
            if  partner_vat:
                error["vat"] = "error"
                error_message.append("VAT already exist")

        return error, error_message
