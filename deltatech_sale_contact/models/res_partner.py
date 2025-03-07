# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    contact_default = fields.Boolean(string="Contact Default", default=False)
    print_green_invoice = fields.Boolean(
        "Green Invoice", default=False, help="If checked, the invoice will not be printed."
    )

    def address_get(self, adr_pref=None):
        res = super().address_get(adr_pref)
        if "delivery" in adr_pref:
            for partner in self:
                for child_id in partner.child_ids.filtered(lambda x: x.type == "delivery"):
                    if child_id.contact_default:
                        res["delivery"] = child_id.id
        if "invoice" in adr_pref:
            for partner in self:
                for child_id in partner.child_ids.filtered(lambda x: x.type == "invoice"):
                    if child_id.contact_default:
                        res["invoice"] = child_id.id
        return res

    def write(self, vals):
        res = super().write(vals)
        if vals.get("contact_default", False):
            for partner in self:
                if partner.parent_id:
                    partner.parent_id.child_ids.filtered(lambda x: x.type == partner.type and x.id != partner.id).write(
                        {"contact_default": False}
                    )
        return res
