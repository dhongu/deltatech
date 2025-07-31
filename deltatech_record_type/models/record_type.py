# ©  2024 Terrabit Solutions
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class RecordType(models.Model):
    _name = "record.type"
    _description = "Record Type"

    name = fields.Char(required=True)
    model = fields.Selection(
        [("sale.order", "Sale Order"), ("purchase.order", "Purchase Order"), ("account.move", "Invoice")],
        string="Model",
    )
    user_ids = fields.Many2many("res.users", string="Allowed Users", domain=[("share", "=", False)])
    default_values_ids = fields.One2many(
        "record.type.default.values", "record_type_id", string="Default Values", copy=True
    )
    route_ids = fields.Many2many("stock.route", "Routes")
    company_id = fields.Many2one("res.company", "Company", default=False)


class SaleOrderTypeDefaultValues(models.Model):
    _name = "record.type.default.values"
    _description = "Sale Order Type Default Values"

    field_id = fields.Many2one("ir.model.fields", domain="[('model_id','=',model_id)]", string="Field")
    field_name = fields.Char(string="Field Name", required=True)
    field_value = fields.Char(string="Field Value", required=True)
    field_type = fields.Selection(
        [("char", "Char"), ("id", "Id"), ("boolean", "Boolean")], string="Field Type", required=True, default="char"
    )
    record_type_id = fields.Many2one("record.type", ondelete="cascade")
    model_id = fields.Many2one("ir.model", compute="_compute_model_id", compute_sudo=True)
    value_ref = fields.Reference(
        "_selection_target_model",
        "Related",
        compute="_compute_resource_ref",
        inverse="_inverse_resource_ref",
        readonly=False,
    )

    @api.depends("field_id", "field_value")
    def _compute_resource_ref(self):
        for item in self:
            if item.field_id.relation and item.field_id.relation in self.env:
                try:
                    if not item.field_value:
                        ref = self.env[item.field_id.relation].search([], limit=1)
                        item.field_value = ref.id
                    item.value_ref = f"{item.field_id.relation},{item.field_value or 0}"
                except Exception:
                    _logger.error("Error while computing resource ref", exc_info=True)
                    item.value_ref = None
            else:
                item.value_ref = None

    def _inverse_resource_ref(self):
        for item in self:
            if item.value_ref:
                item.field_value = item.value_ref.id

    def _selection_target_model(self):
        return [(model.model, model.name) for model in self.env["ir.model"].sudo().search([])]

    @api.depends("record_type_id")
    def _compute_model_id(self):
        for record in self:
            # record.model_id = self.env["ir.model"].sudo().search([("model", "=", record.record_type_id.model)])
            record.model_id = self.env["ir.model"]._get(record.record_type_id.model)

    @api.onchange("field_id")
    def _onchange_field_id(self):
        self.field_name = self.field_id.name
        self.field_value = ""
        if self.field_id.ttype == "many2one":
            self.field_type = "id"
        elif self.field_id.ttype == "char":
            self.field_type = "char"
        elif self.field_id.ttype == "boolean":
            self.field_type = "boolean"
        elif self.field_id.ttype == "selection":
            self.field_type = "char"
        elif self.field_id.ttype == "integer":
            self.field_type = "char"
