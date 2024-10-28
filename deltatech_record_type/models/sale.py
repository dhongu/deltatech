# ©  2015-2021 Terrabit Solutions
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    so_type = fields.Many2one("record.type", string="Type", tracking=True)

    @api.onchange("so_type")
    def _check_so_type(self):
        so_type_selected = self.env["record.type"].search([("id", "=", self.so_type.id), ("model", "=", "sale")])
        if so_type_selected:
            for default_value in so_type_selected.default_values_ids:
                if default_value.field_type == "id":
                    self[default_value.field_name] = int(default_value.field_value)
                if default_value.field_type == "char":
                    self[default_value.field_name] = default_value.field_value
                if default_value.field_type == "boolean":
                    self[default_value.field_name] = default_value.field_value == "True"
