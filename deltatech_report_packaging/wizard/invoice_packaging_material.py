from collections import defaultdict

from odoo import fields, models

from ..constants import PACKAGING_MATERIAL_TYPES


class InvoicePackaging(models.TransientModel):
    _name = "packaging.report.material"
    _description = "Invoice Packaging Material Report"

    state = fields.Selection(
        [("choose", "Choose"), ("get", "Result")],
        default="choose",
        required=True,
    )
    line_ids = fields.One2many(
        "packaging.report.material.line",
        "report_id",
        string="Lines",
    )

    def do_report(self):
        self.ensure_one()
        quantities_by_material = defaultdict(float)
        invoices = self.env["account.move"].browse(self.env.context.get("active_ids", [])).exists()
        for invoice in invoices.filtered(lambda move: move.move_type != "entry"):
            if not invoice.packaging_material_ids:
                invoice.refresh_packaging_material()
            for material in invoice.packaging_material_ids:
                quantities_by_material[material.material_type] += material.qty

        self.line_ids.unlink()
        self.env["packaging.report.material.line"].create(
            [
                {
                    "report_id": self.id,
                    "material_type": material_type,
                    "qty": quantity,
                }
                for material_type, quantity in quantities_by_material.items()
            ]
        )
        self.state = "get"
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }


class InvoicePackagingLine(models.TransientModel):
    _name = "packaging.report.material.line"
    _description = "Invoice Packaging Material Report Line"
    _order = "material_type, id"

    report_id = fields.Many2one(
        "packaging.report.material",
        required=True,
        ondelete="cascade",
    )
    material_type = fields.Selection(PACKAGING_MATERIAL_TYPES, required=True)
    qty = fields.Float(string="Quantity", required=True)
