from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    document_weight_on_sale = fields.Boolean(related="company_id.document_weight_on_sale", readonly=False)
    document_weight_on_invoice = fields.Boolean(related="company_id.document_weight_on_invoice", readonly=False)
    document_weight_gross_only = fields.Boolean(related="company_id.document_weight_gross_only", readonly=False)
    document_weight_propagate_variants = fields.Boolean(
        string="Copy weights to all variants",
        config_parameter="deltatech_document_weight.propagate_variants",
        help="When the weight, the volume or the net weight is set on a product template, write it on all "
        "its variants, and give it to the variants created on demand (dynamic attributes). "
        "By default Odoo only does it for a template with a single variant.",
    )
