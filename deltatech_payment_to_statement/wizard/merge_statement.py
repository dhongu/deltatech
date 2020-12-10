# ©  2020 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class MergeStatement(models.TransientModel):
    """
    The idea behind this wizard is to create a list of potential statement to
    merge. We use two objects, the first one is the wizard for the end-user.
    And the second will contain the object list to merge.
    """

    _inherit = "merge.object.wizard"
    _name = "merge.statement.wizard"
    _description = "Merge Statement Wizard"
    _model_merge = "account.bank.statement"
    _table_merge = "account_bank_statement"

    object_ids = fields.Many2many(_model_merge, string="Statement")
    dst_object_id = fields.Many2one(_model_merge, string="Destination Statement")
