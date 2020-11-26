from odoo import fields, models


class InvoicePackaging(models.TransientModel):
    _name = "invoice.packaging.material"
    _description = "Invoice Packaging Material"

    state = fields.Selection([("choose", "choose"), ("get", "get")], default="choose")
    line_ids = fields.One2many("invoice.packaging.material.line", "report_id", string="Lines")

    def do_raport(self):
        active_ids = self.env.context.get("active_ids", False)
        products = self.env["product.product"]

        qty = {}
        qty_packaging = {}
        invoices = self.env["account.move"].browse(active_ids)
        for invoice in invoices:
            for item in invoice.invoice_line_ids:
                products |= item.product_id
                if item.product_id.id in qty:
                    qty[item.product_id.id] += item.quantity
                else:
                    qty[item.product_id.id] = item.quantity

        for product in products:
            for packaging_material in product.product_tmpl_id.packaging_material_ids:
                q = qty_packaging.get(packaging_material.material_type, 0.0)
                qty_packaging[packaging_material.material_type] = q + qty[product.id] * packaging_material.qty

        lines = []
        for material_type in qty_packaging:
            lines += [{"report_id": self.id, "material_type": material_type, "qty": qty_packaging[material_type]}]

        self.env["invoice.packaging.material.line"].create(lines)

        self.write({"state": "get"})

        return {
            "type": "ir.actions.act_window",
            "res_model": "invoice.packaging.material",
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }


class InvoicePackagingLine(models.TransientModel):
    _name = "invoice.packaging.material.line"
    _description = "Invoice Packaging Material Line"

    report_id = fields.Many2one("invoice.packaging.material")
    material_type = fields.Selection([("plastic", "Plastic"), ("wood", "Wood"), ("paper", "Paper"), ("pet", "Pet")])
    qty = fields.Float(string="Quantity")
