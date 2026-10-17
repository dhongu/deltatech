# © 2025 Deltatech
# See README.rst file on the addons root folder for license details


from odoo import models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        """
        Check if the pickings have complete sets before validate
        :return: super()
        """
        errors = []
        for picking in self:
            error = picking.check_complete_set()
            if error:
                errors.append(error)
        if errors:
            raise UserError("\n".join(errors))

        return super().button_validate()

    def check_complete_set(self):
        """
        Check if one picking has complete sets
        :return: False if all complete sets are present, else return an error message
        """
        self.ensure_one()
        boms_present = self.env["mrp.bom"]
        for line in self.move_ids:
            if (
                line.bom_line_id
                and line.sale_line_id
                and line.bom_line_id.bom_id.type == "phantom"
                and line.bom_line_id.bom_id.restrict_incomplete_delivery
            ):
                boms_present |= line.bom_line_id.bom_id
        # for each bom, check if all bom lines are present in the picking and all the quantities are correct
        for bom in boms_present:
            set_name = bom.product_id.display_name if bom.product_id else bom.product_tmpl_id.display_name
            bom_lines = bom.bom_line_ids
            bom_moves = self.env["stock.move"]
            for bom_line in bom_lines:
                if bom_line.product_id not in self.move_ids.product_id:
                    return self.env._(
                        "Set delivery restriction: missing product %(product)s in picking %(picking)s for set %(set)s",
                        product=bom_line.product_id.name,
                        picking=self.name,
                        set=set_name,
                    )
                bom_moves |= self.move_ids.filtered(lambda move, bom_line=bom_line: move.bom_line_id == bom_line)
            if len(bom_moves) != len(bom_lines):
                return self.env._(
                    "Set delivery restriction: quantities do not match in picking %(picking)s for set %(set)s",
                    picking=self.name,
                    set=set_name,
                )
            # get first line
            picking_qty = bom_moves[0].quantity
            bom_qty = bom_moves[0].bom_line_id.product_qty
            picking_factor = picking_qty / bom_qty if bom_qty else 0
            # check if other lines are correct
            for bom_move in bom_moves[1:]:
                picking_qty_expected = bom_move.bom_line_id.product_qty * picking_factor
                if float_compare(
                    picking_qty_expected, bom_move.quantity, precision_rounding=bom_move.product_uom.rounding
                ):
                    return self.env._(
                        "Set delivery restriction: quantity mismatch for product %(product)s "
                        "in picking %(picking)s for set %(set)s",
                        product=bom_move.product_id.name,
                        picking=self.name,
                        set=set_name,
                    )
        return False
