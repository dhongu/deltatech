# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    hide_picking_image_pdf = fields.Boolean(
        string="Hide Product Images on Transfer PDFs",
        help="Do not print the product image on the delivery slip and on the picking operations report. "
        "The images stay visible on screen.",
    )
