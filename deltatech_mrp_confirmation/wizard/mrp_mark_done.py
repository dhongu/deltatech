# coding=utf-8

from odoo import api, fields, models, tools, registry
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
import threading

class MrpMarkDone(models.TransientModel):
    _name = 'mrp.mark.done'
    _description = 'MRP Mark Done'


    @api.multi
    def do_mark_done(self):
        threaded_calculation = threading.Thread(target=self._do_mark_done, args=())
        threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def _do_mark_done(self):
        active_ids = self.env.context.get('active_ids', False)

        with api.Environment.manage():
            new_cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=new_cr))
            productions = self.env['mrp.production'].browse(active_ids)
            for production in productions:
                if production.check_to_done:
                    production.button_mark_done()
            new_cr.commit()
            new_cr.close()

