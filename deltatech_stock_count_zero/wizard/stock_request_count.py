# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.exceptions import AccessError


class StockRequestCount(models.TransientModel):
    _inherit = "stock.request.count"

    # Same restriction as the standard "Set to 0" / "Apply" of the physical inventory
    set_count_zero = fields.Boolean(string="Set Count to Zero", default=False, groups="stock.group_stock_manager")

    def action_request_count(self):
        # the field is read with sudo: it is restricted to the managers, the check below is the real barrier
        if any(self.sudo().mapped("set_count_zero")) and not self.env.user.has_group("stock.group_stock_manager"):
            raise AccessError(self.env._("Only an inventory administrator can set the counted quantity to zero."))
        action = {}
        for count_request in self:
            if count_request.sudo().set_count_zero:
                # Only the selected quants are set to zero and applied: for tracked products the standard
                # request also adds the sibling quants (all lots of the product in the location).
                quants_to_zero = count_request.quant_ids
                values = count_request._get_values_to_write()
                values["inventory_quantity"] = 0.0
                quants_to_zero.with_context(inventory_mode=True).write(values)
                result = quants_to_zero.with_context(inventory_mode=True).action_apply_inventory()
                if result:
                    # outdated quants: the conflict wizard decides how the count is applied
                    action = result
            else:
                super(StockRequestCount, count_request).action_request_count()
        return action
