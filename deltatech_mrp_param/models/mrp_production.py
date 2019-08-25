# coding=utf-8


from odoo import models, fields, api
import math


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _workorders_create(self, bom, bom_data):
        workorders = super(MrpProduction, self)._workorders_create(bom, bom_data)
        workorders.button_copy_param()

        return workorders
