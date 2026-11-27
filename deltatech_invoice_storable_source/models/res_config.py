# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    check_storable_sale_source = fields.Boolean(
        string="Customer invoices for storable products only from sale orders",
        help="A customer invoice or credit note with a storable product can be posted only if "
        "the line comes from a sale order. Services are not checked.",
    )
    check_storable_purchase_source = fields.Boolean(
        string="Vendor bills for storable products only from purchase orders",
        help="A vendor bill or refund with a storable product can be posted only if "
        "the line comes from a purchase order. Services are not checked.",
    )


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    check_storable_sale_source = fields.Boolean(
        related="company_id.check_storable_sale_source",
        readonly=False,
    )
    check_storable_purchase_source = fields.Boolean(
        related="company_id.check_storable_purchase_source",
        readonly=False,
    )
