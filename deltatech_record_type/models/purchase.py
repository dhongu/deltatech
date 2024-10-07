# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "purchase.order"

    po_type = fields.Many2one("record.type", string="Type", tracking=True)

    @api.onchange("po_type")
    def _check_po_type(self):
        po_type_selected = self.env["record.type"].search([("id", "=", self.po_type.id), ("model", "=", "purchase")])
        if po_type_selected:
            for default_value in po_type_selected.default_values_ids:
                if default_value.field_type == "id":
                    self[default_value.field_name] = int(default_value.field_value)
                if default_value.field_type == "char":
                    self[default_value.field_name] = default_value.field_value
                if default_value.field_type == "boolean":
                    self[default_value.field_name] = default_value.field_value == "True"
