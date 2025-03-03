# ©  20023-Now Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


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
                if self.env.user not in group_id.users:
                    raise UserError(_("Your user cannot validate this type of transfer"))

            # new product or wrong quantities check
            if picking.picking_type_id.restrict_quantities or picking.picking_type_id.restrict_new_products:
                precision = self.env["decimal.precision"].precision_get("Product Unit of Measure")
                for move_line in picking.move_line_ids_without_package:
                    if (
                        picking.picking_type_id.restrict_quantities
                        and move_line.quantity_product_uom
                        and float_compare(
                            move_line.quantity_product_uom,
                            move_line.quantity,
                            precision_digits=precision,
                        )
                        != 0
                    ):
                        raise UserError(
                            _("Done quantities not equal to reserved for [%(product_code)s] %(product_name)s")
                            % {
                                "product_code": move_line.product_id.default_code,
                                "product_name": move_line.product_id.name,
                            }
                        )
                    if (
                        picking.picking_type_id.restrict_new_products
                        and float_compare(move_line.quantity_product_uom, 0.0, precision_digits=precision) == 0
                        and float_compare(move_line.quantity, 0.0, precision_digits=precision) != 0
                    ):
                        raise UserError(
                            _("Unrecognized product: [%(product_code)s] %(product_name)s")
                            % {
                                "product_code": move_line.product_id.default_code,
                                "product_name": move_line.product_id.name,
                            }
                        )
        return super().button_validate()
