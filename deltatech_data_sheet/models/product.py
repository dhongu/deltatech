# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # {'default_public':True,'default_res_model':'ir.ui.view'}
    data_sheet_id = fields.Many2one(
        "ir.attachment",
        string="Data Sheet Attachment",
        domain=[("mimetype", "=", "application/pdf"), ("public", "=", True)],
    )

    safety_data_sheet_id = fields.Many2one(
        "ir.attachment",
        string="Safety Data Sheet",
        domain=[("mimetype", "=", "application/pdf"), ("public", "=", True)],
    )
