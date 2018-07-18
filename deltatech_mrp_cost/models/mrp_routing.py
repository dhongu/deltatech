 # -*- coding: utf-8 -*-
# ©  2015-2017 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com   
# See README.rst file on addons root folder for license details



from odoo import models, fields, api


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'


    @api.multi
    def get_time_cycle(self, quantity, product=None ):
        'returneaza timpul per unitate'
        self.ensure_one()
        return self.time_cycle
