# coding=utf-8

from odoo import api, fields, models, tools, registry
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
import threading

class MrpCheckAvailability(models.TransientModel):
    _name = 'mrp.check.availability'
    _description = 'Check Availability'


    @api.multi
    def do_check_availability(self):
        threaded_calculation = threading.Thread(target=self._do_check_availability, args=())
        threaded_calculation.start()

        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def _do_check_availability(self):
        active_ids = self.env.context.get('active_ids', False)
        with api.Environment.manage():
            new_cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=new_cr))
            productions = self.env['mrp.production'].browse(active_ids)
            productions._compute_availability()
            self.env.cr.commit()
            self._cr.close()

