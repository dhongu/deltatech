from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAttribute(WebsiteSale):
    def _checkout_form_save(self, mode, checkout, all_values):
        partner_id = super()._checkout_form_save(mode, checkout, all_values)

        Partner = request.env["res.partner"]
        partner_id = Partner.browse(partner_id)
        if partner_id.company_name and partner_id.vat:
            if not partner_id.parent_id:
                values = {
                    "name": partner_id.company_name,
                    "is_company": True,
                    "vat": partner_id.vat,
                    "city": partner_id.city,
                    "state_id": partner_id.state_id.id,
                    "country_id": partner_id.country_id.id,
                    "street": partner_id.street,
                }
                company_partner_id = Partner.sudo().with_context(tracking_disable=True).create(values)
                partner_id.sudo().write({"parent_id": company_partner_id.id})

            order = request.website.sale_get_order()
            order.partner_invoice_id = partner_id.commercial_partner_id
        return partner_id.id
