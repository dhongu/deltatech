# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import UserError


class StockDisassembly(models.Model):
    _inherit = "stock.disassembly"

    bom_id = fields.Many2one(
        "mrp.bom",
        string="Bill of Materials",
        compute="_compute_bom_id",
        store=True,
        readonly=False,
        precompute=True,
        check_company=True,
        domain="['&', '|', ('product_id', '=', product_id), '&', ('product_id', '=', False), "
        "('product_tmpl_id.product_variant_ids', 'in', product_id), ('type', '=', 'normal')]",
        help="Optional: the resulting products can be filled in from the components of this bill of "
        "materials, then changed freely.",
    )

    @api.depends("product_id", "company_id")
    def _compute_bom_id(self):
        for disassembly in self:
            if not disassembly.product_id:
                disassembly.bom_id = False
                continue
            boms = self.env["mrp.bom"]._bom_find(
                disassembly.product_id, company_id=disassembly.company_id.id, bom_type="normal"
            )
            disassembly.bom_id = boms[disassembly.product_id]

    def action_load_bom(self):
        """Replace the product lines by the components of the bill of materials, for the quantity
        disassembled; kits are exploded down to their components. The loss lines are kept."""
        for disassembly in self:
            if disassembly.state != "draft":
                raise UserError(self.env._("Only a draft disassembly report can be filled in."))
            bom = disassembly.bom_id
            if not bom:
                raise UserError(self.env._("Select a bill of materials."))
            qty = disassembly.product_uom_id._compute_quantity(disassembly.product_qty, bom.uom_id)
            _boms, lines = bom.explode(disassembly.product_id, qty / bom.product_qty)
            disassembly.line_ids.filtered(lambda line: line.line_type == "product").unlink()
            vals_list = []
            sequence = 10
            for bom_line, line_data in lines:
                if bom_line.product_id.type == "service" or not line_data["qty"]:
                    continue
                vals_list.append(
                    {
                        "disassembly_id": disassembly.id,
                        "sequence": sequence,
                        "line_type": "product",
                        "product_id": bom_line.product_id.id,
                        "quantity": line_data["qty"],
                        "product_uom_id": bom_line.uom_id.id,
                    }
                )
                sequence += 1
            self.env["stock.disassembly.line"].create(vals_list)
        return True
