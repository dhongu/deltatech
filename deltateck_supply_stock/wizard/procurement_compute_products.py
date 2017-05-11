# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import threading

from odoo import api, fields, models, tools, registry

_logger = logging.getLogger(__name__)


class ProcurementComputeProducts(models.TransientModel):
    _name = 'procurement.compute.products'
    _description = 'Compute schedulers'


    product_ids = fields.Many2many('product.product')


    @api.model
    def default_get(self, fields):
        defaults = super(ProcurementComputeProducts, self).default_get(fields)
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', False)

        if active_model == 'product.product':
            domain = [('id', 'in', active_ids)]
        if active_model == 'product.template':
            domain = [('product_tmpl_id', 'in', active_ids)]

        res = self.env['product.product'].search(domain)
        defaults['product_ids'] = [(6, 0, [rec.id for rec in res])]
        return defaults


    @api.multi
    def _procure_calculation_products(self):
        with api.Environment.manage():
            # As this function is in a new thread, i need to open a new cursor, because the old one may be closed
            new_cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=new_cr))  # TDE FIXME
            scheduler_cron = self.sudo().env.ref('procurement.ir_cron_scheduler_action')
            # Avoid to run the scheduler multiple times in the same time
            try:
                with tools.mute_logger('odoo.sql_db'):
                    self._cr.execute("SELECT id FROM ir_cron WHERE id = %s FOR UPDATE NOWAIT", (scheduler_cron.id,))
            except Exception:
                _logger.info('Attempt to run procurement scheduler aborted, as already running')
                self._cr.rollback()
                self._cr.close()
                return {}

            Procurement = self.env['procurement.order']
            for company in self.env.user.company_ids:
                Procurement.supply(self.product_ids, use_new_cursor=self._cr.dbname, company_id=company.id)
            # close the new cursor
            self._cr.close()
            return {}

    @api.multi
    def procure_calculation(self):
        threaded_calculation = threading.Thread(target=self._procure_calculation_products, args=())
        threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}
