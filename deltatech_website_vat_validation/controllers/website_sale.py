# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleVATValidation(WebsiteSale):
    def _validate_address_values(
        self,
        address_values,
        partner_sudo,
        address_type,
        use_delivery_as_billing,
        required_fields,
        is_main_address,
        **_kwargs,
    ):
        for field in ["vat", "email", "phone"]:
            if address_values.get(field):
                address_values[field] = address_values.get(field).strip()

        invalid_fields, missing_fields, error_messages = super()._validate_address_values(
            address_values,
            partner_sudo,
            address_type,
            use_delivery_as_billing,
            required_fields,
            is_main_address,
            **_kwargs,
        )
        partner = partner_sudo or request.env["res.users"].browse(request.uid).partner_id
        for field in ["vat", "email", "phone"]:
            value = address_values.get(field, False)
            if value and field not in invalid_fields:
                domain = [(field, "=", value), ("id", "!=", partner.id), ("parent_id", "=", False)]
                partner_exists = request.env["res.partner"].sudo().search(domain, limit=1)
                if partner_exists:
                    invalid_fields.add(field)
                    error_messages.append(_("An other partner already exists with the same %s", value))

        return invalid_fields, missing_fields, error_messages
