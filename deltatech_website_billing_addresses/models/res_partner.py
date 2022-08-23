# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    access_for_user_id = fields.Many2one("res.users", ondelete="set null")
    user_address_ids = fields.Many2many("res.partner", compute="_compute_user_address_ids", readonly=True)
    contact_type = fields.Selection(
        [
            ("contact", "Contact"),
            ("company", "Company"),
            ("billing_address", "Billing address"),
            ("shipping_address", "Shipping address"),
        ],
        compute="_compute_contact_type",
    )

    def _compute_user_address_ids(self):
        for partner in self:
            domain = [("partner_id", "=", partner.id)]
            user = self.env["res.users"].search(domain)
            address = self.env["res.partner"]
            if user:
                address = self.env["res.partner"].search([("access_for_user_id", "=", user.id)])
                address -= partner.child_ids
            partner.user_address_ids = address

    def _compute_contact_type(self):
        for partner in self:
            if partner.is_company:
                partner.contact_type = "company"
            elif partner.type == "invoice":
                partner.contact_type = "billing_address"
            elif partner.type == "delivery":
                partner.contact_type = "shipping_address"
            else:
                partner.contact_type = "contact"
