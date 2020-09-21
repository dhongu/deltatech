# -*- coding: utf-8 -*-

from odoo.osv import fields, osv
from odoo.tools.float_utils import float_compare, float_round
import odoo.addons.decimal_precision as dp
class stock_quant(osv.osv):
    _inherit = "stock.quant"
    def _calc_unit_value(self, cr, uid, ids, name, attr, context=None):
        context = dict(context or {})
        res = {}
        uid_company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        for quant in self.browse(cr, uid, ids, context=context):
            context.pop('force_company', None)
            if quant.company_id.id != uid_company_id:
                #if the company of the quant is different than the current user company, force the company in the context
                #then re-do a browse to read the property fields for the good company.
                context['force_company'] = quant.company_id.id
                quant = self.browse(cr, uid, quant.id, context=context)
            res[quant.id] = self._get_inventory_value(cr, uid, quant, context=context)/quant.qty
        return res
    _columns = {
                'unit_price': fields.function(_calc_unit_value, string="Pret unitar", type='float', readonly=True),
    }