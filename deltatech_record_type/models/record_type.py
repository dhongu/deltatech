from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrderType(models.Model):
    _name = "record.type"

    name = fields.Char()
    model = fields.Selection(
        [
            ("sale", "Sale Order"),
            ("purchase", "Purchase Order"),
        ],
        string="Model",
    )
    is_default = fields.Boolean()
    default_values_ids = fields.One2many("record.type.default.values", "record_type_id", string="Default Values")

    def write(self, vals):
        if "is_default" in vals and vals.get("is_default", False):
            other_types = self.env["record.type"].search(
                [("is_default", "=", True), ("id", "!=", self.id), ("model", "=", self.model)]
            )
            if other_types:
                raise UserError(_("You cannot have more than one default type."))
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "is_default" in vals and vals.get("is_default", False):
                other_types = self.env["record.type"].search(
                    [("is_default", "=", True), ("id", "!=", self.id), ("model", "=", vals.get("model"))]
                )
                if other_types:
                    raise UserError(_("You cannot have more than one default type."))
        return super().create(vals_list)


class SaleOrderTypeDefaultValues(models.Model):
    _name = "record.type.default.values"
    _description = "Sale Order Type Default Values"

    field_name = fields.Char(string="Field Name", required=True)
    field_value = fields.Char(string="Field Value", required=True)
    field_type = fields.Selection(
        [("char", "Char"), ("id", "Id"), ("boolean", "Boolean")], string="Field Type", required=True
    )
    record_type_id = fields.Many2one("record.type", ondelete="cascade", invisible=True)
