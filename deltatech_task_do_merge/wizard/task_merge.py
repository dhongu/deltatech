# ©  2020 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class MergeTask(models.TransientModel):
    """
        The idea behind this wizard is to create a list of potential task to
        merge. We use two objects, the first one is the wizard for the end-user.
        And the second will contain the object list to merge.
    """

    _inherit = "merge.object.wizard"
    _name = "merge.task.wizard"
    _description = "Merge Task Wizard"
    _model_merge = "project.task"
    _table_merge = "project_task"

    object_ids = fields.Many2many(_model_merge, string="Task")
    dst_object_id = fields.Many2one(_model_merge, string="Destination Task")
