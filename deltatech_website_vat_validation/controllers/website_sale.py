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

        # Integrare ANAF
        if address_values.get("vat") and "vat" not in invalid_fields:
            if address_type == "billing" or use_delivery_as_billing:
                country = request.env["res.country"].sudo().browse(address_values.get("country_id"))
                if country and country.code == "RO":
                    vat = address_values["vat"].strip().upper()
                    if vat.startswith("RO"):
                        vat = vat[2:]
                    if vat.isdigit():
                        res_partner_sudo = request.env["res.partner"].sudo()
                        if hasattr(res_partner_sudo, "_get_Anaf") and hasattr(res_partner_sudo, "_Anaf_to_Odoo"):
                            anaf_error, result = res_partner_sudo._get_Anaf(vat)
                            if not anaf_error and result:
                                anaf_data = res_partner_sudo._Anaf_to_Odoo(result)
                                # Actualizăm valorile adresei cu datele de la ANAF
                                for field in ["name", "street", "city", "zip"]:
                                    if anaf_data.get(field):
                                        address_values[field] = anaf_data[field]
                                if anaf_data.get("state_id") and not address_values.get("state_id"):
                                    address_values["state_id"] = anaf_data["state_id"].id

                                if anaf_data.get("company_type") == "company":
                                    address_values["is_company"] = True
                            else:
                                invalid_fields.add("vat")
                                error_messages.append(_("The VAT number is not valid according to ANAF"))
                    else:
                        invalid_fields.add("vat")
                        error_messages.append(_("The VAT number must contain only digits (after the country code)"))

        for field in ["vat", "email", "phone"]:
            value = address_values.get(field, False)
            if value and field not in invalid_fields:
                domain = [(field, "=", value), ("id", "!=", partner.id), ("parent_id", "=", False)]
                partner_exists = request.env["res.partner"].sudo().search(domain, limit=1)
                if partner_exists:
                    invalid_fields.add(field)
                    error_messages.append(_("An other partner already exists with the same %s", value))

        return invalid_fields, missing_fields, error_messages
