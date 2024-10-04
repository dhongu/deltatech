# ©  2015-2021 Terrabit Solutions
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    so_type = fields.Many2one("record.type", string="Type")

    def _check_so_type(self, vals):
        if "so_type" in vals:
            so_type_selected = self.env["record.type"].search([("id", "=", vals["so_type"]), ("model", "=", "sale")])
            if so_type_selected:
                for default_value in so_type_selected.default_values_ids:
                    if default_value.field_type == "id":
                        vals[default_value.field_name] = int(default_value.field_value)
                    if default_value.field_type == "char":
                        vals[default_value.field_name] = default_value.field_value
                    if default_value.field_type == "boolean":
                        vals[default_value.field_name] = default_value.field_value == "True"

    def write(self, vals):
        self._check_so_type(vals)
        res = super().write(vals)

        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_so_type(vals)
        res = super().create(vals_list)
        return res