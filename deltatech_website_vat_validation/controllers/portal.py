# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.http import request
from odoo import _
from odoo.addons.phone_validation.tools import phone_validation
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalVATValidation(CustomerPortal):
    def details_form_validate(self, data, partner_creation=False):

        for field in ['vat', 'email', 'phone']:
            if field in data and data.get(field):
                data[field] = data.get(field).strip()

        error, error_message = super().details_form_validate(data, partner_creation)

        partner = request.env['res.users'].browse(request.uid).partner_id

        for field in ['vat', 'email', 'phone']:
            value = data.get(field, False)
            if value and field not in error:
                domain = [(field, "=", value), ('id', '!=', partner.id), ('parent_id', '=', False)]
                partner_exists = request.env['res.partner'].search(domain, limit=1)
                if partner_exists:
                    error[field] = "error"
                    error_message.append(_(f"An other partner already exists with the same {value}"))


        return error, error_message
