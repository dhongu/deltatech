# ©  2020 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class UoMProduct(models.TransientModel):
    """
    The idea behind this wizard is to create a list of potential statement to
    merge. We use two objects, the first one is the wizard for the end-user.
    And the second will contain the object list to merge.
    """

    _inherit = "merge.object.wizard"
    _name = "merge.uom.wizard"
    _description = "Merge UoM Wizard"
    _model_merge = "uom.uom"
    _table_merge = "uom_uom"

    object_ids = fields.Many2many(_model_merge, string="UoM")
    dst_object_id = fields.Many2one(_model_merge, string="Destination UoM")
