# ©  2015-2021 Terrabit Solutions
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    so_type = fields.Many2one("sale.order.type", string="Type")


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.model
    def default_get(self, fields_list):
        defaults = super(SaleAdvancePaymentInv, self).default_get(fields_list)
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

    name = fields.Char()
    is_default = fields.Boolean()
    journal_id = fields.Many2one("account.journal", domain=[("type", "=", "sale")])

    def write(self, vals):
        if "is_default" in vals and vals.get("is_default", False):
            other_types = self.env["sale.order.type"].search([("is_default", "=", True), ("id", "!=", self.id)])
            if other_types:
                raise UserError(_("You cannot have more than one default type."))
        return super(SaleOrderType, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "is_default" in vals and vals.get("is_default", False):
                other_types = self.env["sale.order.type"].search([("is_default", "=", True), ("id", "!=", self.id)])
                if other_types:
                    raise UserError(_("You cannot have more than one default type."))
        return super(SaleOrderType, self).create(vals_list)
