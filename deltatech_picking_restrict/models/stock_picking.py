# ©  20023-Now Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models
from odoo.exceptions import UserError


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    validate_group_id = fields.Many2one("res.groups", string="Group for validation")
    restrict_quantities = fields.Boolean(
        string="Restrict done quantities to reserved",
        default=False,
        help="If set, no picking with different reserved quantity and done quantity can be validated",
    )
    restrict_new_products = fields.Boolean(
        string="Restrict new products",
        default=False,
        help="If set, no picking with extra products and done quantity can be validated",
    )


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        for picking in self:
            if picking.picking_type_id.validate_group_id:
                group_id = picking.picking_type_id.validate_group_id
                if self.env.user not in group_id.user_ids:
                    raise UserError(self.env._("Your user cannot validate this type of transfer"))

            # new product or wrong quantities check
            if picking.picking_type_id.restrict_quantities or picking.picking_type_id.restrict_new_products:
                for move in picking.move_ids.filtered(lambda m: m.state != "cancel"):
                    # quantity and product_uom_qty are both expressed in the move unit of measure
                    is_new = move.additional or move.product_uom.is_zero(move.product_uom_qty)
                    if (
                        picking.picking_type_id.restrict_new_products
                        and is_new
                        and not move.product_uom.is_zero(move.quantity)
                    ):
                        raise UserError(
                            self.env._(
                                "Unrecognized product: [%(product_code)s] %(product_name)s",
                                product_code=move.product_id.default_code,
                                product_name=move.product_id.name,
                            )
                        )
                    if (
                        picking.picking_type_id.restrict_quantities
                        and not is_new
                        and move.product_uom.compare(move.quantity, move.product_uom_qty) != 0
                    ):
                        raise UserError(
                            self.env._(
                                "Done quantities not equal to reserved for [%(product_code)s] %(product_name)s",
                                product_code=move.product_id.default_code,
                                product_name=move.product_id.name,
                            )
                        )
        return super().button_validate()
