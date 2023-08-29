# ©  20023-Now Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    validate_group_id = fields.Many2one("res.groups", string="Group for validation")


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        for picking in self:
            if picking.picking_type_id.validate_group_id:
                group_id = picking.picking_type_id.validate_group_id
                if self.env.user not in group_id.users:
                    raise UserError(_("Your user cannot validate this type of transfer"))
        return super().button_validate()
