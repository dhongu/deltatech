# ©  2008-now Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class AddMultiMrpLines(models.TransientModel):
    _name = "add.multi.mrp.lines"
    _description = "Add multiple lines to mrp"

    simple_mrp_id = fields.Many2one("mrp.simple")
    qty = fields.Float(digits="Product Unit of Measure", default=1)
    product_lines = fields.One2many("add.multi.mrp.lines.product", "multi_id", string="Products")

    def add_products(self):
        vals = []
        for line in self.product_lines:
            for product in line.product_ids:
                val = {
                    "product_id": product.id,
                    "uom_id": product.uom_id.id,
                    "quantity": self.qty,
                    "mrp_simple_id": self.simple_mrp_id.id,
                }
                vals.append(val)
                out_line = self.simple_mrp_id.product_out_ids.new(val)
                out_line.onchange_product_id()
                self.simple_mrp_id.product_out_ids |= out_line
        return True

    @api.model
    def default_get(self, fields_list):
        res = super(AddMultiMrpLines, self).default_get(fields_list)
        active_ids = self.env.context.get("active_ids", [])
        if active_ids:
            res["simple_mrp_id"] = active_ids
        return res


class AddMultiSaleLinesProduct(models.TransientModel):
    _name = "add.multi.mrp.lines.product"
    _description = "Add multiple lines to mrp"

    multi_id = fields.Many2one("add.multi.mrp.lines")
    product_ids = fields.Many2many("product.product", string="Product")
