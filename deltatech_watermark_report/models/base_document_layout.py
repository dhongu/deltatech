# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BaseDocumentLayout(models.TransientModel):
    _inherit = "base.document.layout"

    watermark_image = fields.Binary(related="company_id.watermark_image", readonly=False)
