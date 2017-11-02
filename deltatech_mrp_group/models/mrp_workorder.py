# coding=utf-8
# coding=utf-8


from odoo import models, fields, api, _


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    procurement_group_id = fields.Many2one( 'procurement.group', 'Procurement Group', related='production_id.procurement_group_id')