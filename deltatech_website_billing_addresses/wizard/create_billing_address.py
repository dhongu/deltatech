# ©  2008-2022 Deltatech
#              Dan Stoica<danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import UserError


class CreateBillingAddress(models.TransientModel):
    _name = "create.billing.address"
    _description = "Create Billing Address Wizard"

    from_partner = fields.Many2one("res.partner")
    user_id = fields.Many2one("res.users")
    update_vat = fields.Boolean(string="Update VAT")
    vat = fields.Char("VAT")

    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id", [])
        partner_id = self.env["res.partner"].browse(active_id)
        if not partner_id.is_company:
            raise UserError(_("You can only create a billing address from a company!"))
        if partner_id.parent_id:
            raise UserError(_("You cannot create a billing adress on a child partner!"))
        defaults["from_partner"] = partner_id.id
        defaults["vat"] = partner_id.vat
        return defaults

    def create_address(self):
        if self.update_vat:
            vat = self.vat
            self.from_partner.write({"vat": self.vat})
        else:
            vat = self.from_partner.vat
        values = {
            "name": self.user_id.name,
            "vat": vat,
            "parent_id": self.from_partner.id,
            "commercial_partner_id": self.from_partner.id,
            "commercial_company_name": self.from_partner.name,
            "company_name": self.from_partner.name,
            "l10n_ro_vat_number": vat,
            "access_for_user_id": self.user_id.id,
            "street": self.from_partner.street,
            "city": self.from_partner.city,
            "city_id": self.from_partner.city_id.id,
            "state_id": self.from_partner.state_id.id,
            "zip": self.from_partner.zip,
            "country_id": self.from_partner.country_id.id,
            "phone": self.from_partner.phone,
            "type": "invoice",
            "is_company": False,
        }
        res = self.env["res.partner"].create(values)
        return res
