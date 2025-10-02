# © 2025 Deltatech
# See README.rst file on the addons root folder for license details


from odoo import _, models
from odoo.exceptions import UserError


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
        error = False
        boms_present = self.env["mrp.bom"]
        for line in self.move_ids:
            if (
                line.bom_line_id
                and line.sale_line_id
                and line.bom_line_id.bom_id.type == "phantom"
                and line.bom_line_id.bom_id.restrict_incomplete_delivery
            ):
                boms_present |= line.bom_line_id.bom_id
        if not boms_present:
            return error
        # for each bom, check if all bom lines are present in the picking and all the quantities are correct
        for bom in boms_present:
            bom_lines = bom.bom_line_ids
            bom_moves = self.env["stock.move"]
            for bom_line in bom_lines:
                if bom_line.product_id not in self.move_ids.mapped("product_id"):
                    error = _(
                        "Set delivery restriction: missing product %(product)s in picking %(picking)s for set %(set)s"
                    ) % {
                        "product": bom_line.product_id.name,
                        "picking": self.name,
                        "set": bom.product_id.display_name if bom.product_id else bom.product_tmpl_id.display_name,
                    }
                    break
                else:
                    bom_moves |= self.move_ids.filtered(lambda move: move.bom_line_id == bom_line)
            if len(bom_moves) != len(bom_lines):
                error = _(
                    "Set delivery restriction: quantities do not match in picking %(picking)s for set %(set)s"
                ) % {
                    "picking": self.name,
                    "set": bom.product_id.display_name if bom.product_id else bom.product_tmpl_id.display_name,
                }
            # get first line
            picking_qty = bom_moves[0].quantity
            bom_qty = bom_lines.filtered(lambda line: line.product_id == bom_moves[0].product_id).product_qty
            picking_factor = picking_qty / bom_qty if bom_qty else 0
            # check if other lines are correct
            for bom_move in bom_moves[1:]:
                picking_qty_expected = bom_move.bom_line_id.product_qty * picking_factor
                if picking_qty_expected != bom_move.quantity:
                    error = _(
                        "Set delivery restriction: quantity mismatch for product %(product)s in picking %(picking)s for set %(set)s"
                    ) % {
                        "product": bom_move.product_id.name,
                        "picking": self.name,
                        "set": bom.product_id.display_name if bom.product_id else bom.product_tmpl_id.display_name,
                    }
                    break
            if error:
                break
        return error
