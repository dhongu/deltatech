# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import json

from odoo.http import request
from odoo.tools import str2bool

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.website_sale.controllers.main import WebsiteSale


class TbAddressNameMixin:
    """The address form asks the last name and the first name in two fields; the partner
    keeps them together in its name, last name first."""

    def _parse_form_data(self, form_data):
        if "tb_lastname" in form_data or "tb_firstname" in form_data:
            parts = [(form_data.get(key) or "").strip() for key in ("tb_lastname", "tb_firstname")]
            form_data["name"] = " ".join(part for part in parts if part)
        return super()._parse_form_data(form_data)

    def _validate_address_values(
        self,
        address_values,
        partner_sudo,
        address_type,
        use_delivery_as_billing,
        required_fields,
        **kwargs,
    ):
        invalid_fields, missing_fields, error_messages = super()._validate_address_values(
            address_values,
            partner_sudo,
            address_type,
            use_delivery_as_billing,
            required_fields,
            **kwargs,
        )
        if "name" in missing_fields:
            # The name is typed in the last name and first name fields: those are highlighted.
            missing_fields.update({"tb_lastname", "tb_firstname"})
        return invalid_fields, missing_fields, error_messages


class TbCustomerPortal(TbAddressNameMixin, CustomerPortal):
    pass


class TbWebsiteSale(TbAddressNameMixin, WebsiteSale):
    # Registered office fields of the billing section, by the `res.partner` field they fill.
    TB_COMPANY_ADDRESS_FIELDS = {
        "state_id": "tb_company_state_id",
        "city": "tb_company_city",
        "street": "tb_company_street",
        "zip": "tb_company_zip",
    }

    def _tb_company_address_values(self, form_data):
        """The registered office typed in the billing section, as `res.partner` values."""
        values = {}
        for fname, form_name in self.TB_COMPANY_ADDRESS_FIELDS.items():
            value = (form_data.get(form_name) or "").strip()
            if fname == "state_id":
                # Only a county of Romania, the country of the registered office; any other id
                # is dropped and the county is then reported as missing.
                state = request.env["res.country.state"].sudo().browse(int(value)) if value.isdigit() else None
                value = state.id if state and state.exists() and state.country_id.code == "RO" else False
            values[fname] = value or False
        return values

    def _validate_address_values(
        self,
        address_values,
        partner_sudo,
        address_type,
        use_delivery_as_billing,
        required_fields,
        **kwargs,
    ):
        invalid_fields, missing_fields, error_messages = super()._validate_address_values(
            address_values,
            partner_sudo,
            address_type,
            use_delivery_as_billing,
            required_fields,
            **kwargs,
        )
        if not str2bool(kwargs.get("tb_company") or "false"):
            return invalid_fields, missing_fields, error_messages
        Partner = request.env["res.partner"]
        romania = request.env.ref("base.ro")
        # The fiscal position of the order follows the customer and the delivery address, not
        # the invoice address: a Romanian company is invoiced the domestic VAT only when the
        # goods are delivered in Romania, so the company billing is limited to those.
        if address_type == "delivery" or use_delivery_as_billing:
            delivery_country_id = address_values.get("country_id")
        else:
            delivery_country_id = request.cart.partner_shipping_id.country_id.id
        if delivery_country_id and delivery_country_id != romania.id:
            invalid_fields.add("tb_company")
            error_messages.append(request.env._("Billing to a company is available only for deliveries in Romania."))
        company_missing = {
            fname for fname in ("tb_company_name", "tb_company_vat") if not (kwargs.get(fname) or "").strip()
        }
        vat = kwargs.get("tb_company_vat")
        if "tb_company_vat" not in company_missing and not Partner._tb_is_valid_company_vat(vat):
            invalid_fields.add("tb_company_vat")
            error_messages.append(request.env._("The company VAT number (CUI) is not valid."))
        # The invoice address is the registered office, a complete address in Romania. It is
        # asked whether or not the company is already recorded, so the form does not tell
        # a visitor which VAT numbers belong to our customers.
        address = self._tb_company_address_values(kwargs)
        for fname in self._get_mandatory_address_fields(romania) - {"country_id"}:
            if not address.get(fname):
                company_missing.add(self.TB_COMPANY_ADDRESS_FIELDS[fname])
        if company_missing:
            missing_fields |= company_missing
            error_messages.append(
                request.env._("Fill in the company details: name, VAT number (CUI) and registered office.")
            )
        return invalid_fields, missing_fields, error_messages

    def _prepare_checkout_page_values(self, order_sudo, **kwargs):
        """The invoice address created under a company already recorded (billing section)
        is not one of the customer's addresses: it is added to the billing choices, so the
        checkout shows it selected instead of the customer's own address."""
        values = super()._prepare_checkout_page_values(order_sudo, **kwargs)
        invoice_address = order_sudo.partner_invoice_id
        billing_addresses = values.get("billing_addresses")
        if invoice_address and billing_addresses is not None and invoice_address not in billing_addresses:
            values["billing_addresses"] = invoice_address.with_context(show_address=1) | billing_addresses
        return values

    def shop_address_submit(
        self, partner_id=None, address_type="billing", use_delivery_as_billing=None, callback=None, **form_data
    ):
        result = super().shop_address_submit(
            partner_id=partner_id,
            address_type=address_type,
            use_delivery_as_billing=use_delivery_as_billing,
            callback=callback,
            **form_data,
        )
        is_billing = address_type == "billing" or str2bool(use_delivery_as_billing or "false")
        if not (is_billing and str2bool(form_data.get("tb_company") or "false")):
            return result
        # Through the route the result is already an HTTP response holding the JSON feedback.
        feedback = result.get_data(as_text=True) if hasattr(result, "get_data") else result
        if "invalid_fields" in json.loads(feedback):
            return result
        order_sudo = request.cart
        if not order_sudo or not order_sudo.partner_id or order_sudo._is_anonymous_cart():
            return result
        invoice_address = order_sudo._tb_prepare_invoice_company(
            (form_data.get("tb_company_name") or "").strip(),
            form_data.get("tb_company_vat"),
            address=self._tb_company_address_values(form_data),
        )
        # The cart update of the standard checkout; the fiscal position does not depend on the
        # invoice address (see the delivery country check of the validation).
        order_sudo._update_address(invoice_address.id, {"partner_invoice_id"})
        return result
