from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    document_weight_on_sale = fields.Boolean(
        string="Weights on quotations",
        default=True,
        help="Print the net weight, the gross weight and the volume under each product and in total on "
        "the quotation / sales order report.",
    )
    document_weight_on_invoice = fields.Boolean(
        string="Weights on invoices",
        help="Print the net weight, the gross weight and the volume under each product and in total on "
        "the customer invoice.",
    )
