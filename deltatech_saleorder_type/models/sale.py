# ©  2015-2021 Terrabit Solutions
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    so_type = fields.Many2one("sale.order.type", string="Type")

    def _check_so_type(self, vals):
        if "so_type" in vals:
            so_type_selected = self.env["sale.order.type"].search(
                [("id", "=", vals["so_type"]), ("model", "=", "sale")]
            )
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


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_ids = self._context["active_ids"]
        if active_ids:
            order = self.env["sale.order"].browse(self._context.get("active_ids"))[0]
            if order and order.so_type:
                journal_id = order.so_type.journal_id
                if journal_id:
                    defaults["journal_id"] = journal_id.id
        return defaults


class SaleOrderType(models.Model):
    _name = "sale.order.type"
    _description = "SaleOrderType"

    name = fields.Char()
    is_default = fields.Boolean()
    journal_id = fields.Many2one("account.journal", domain=[("type", "=", "sale")])
    model = fields.Selection(
        [
            ("sale", "Sale Order"),
            ("purchase", "Purchase Order"),
            ("picking", "Picking Order"),
            ("production", "Production Order"),
        ],
        string="Model",
    )
    default_values_ids = fields.One2many(
        "sale.order.type.default.values", "sale_order_type_id", string="Default Values"
    )

    def write(self, vals):
        if "is_default" in vals and vals.get("is_default", False):
            other_types = self.env["sale.order.type"].search([("is_default", "=", True), ("id", "!=", self.id)])
            if other_types:
                raise UserError(_("You cannot have more than one default type."))
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "is_default" in vals and vals.get("is_default", False):
                other_types = self.env["sale.order.type"].search([("is_default", "=", True), ("id", "!=", self.id)])
                if other_types:
                    raise UserError(_("You cannot have more than one default type."))
        return super().create(vals_list)


class SaleOrderTypeDefaultValues(models.Model):
    _name = "sale.order.type.default.values"
    _description = "Sale Order Type Default Values"

    field_name = fields.Char(string="Field Name", required=True)
    field_value = fields.Char(string="Field Value", required=True)
    field_type = fields.Selection(
        [("char", "Char"), ("id", "Id"), ("boolean", "Boolean")], string="Field Type", required=True
    )
    sale_order_type_id = fields.Many2one("sale.order.type", ondelete="cascade", invisible=True)
