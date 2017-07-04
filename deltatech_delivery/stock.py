from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api


class stock_picking_type(models.Model):
    _inherit = "stock.picking.type"

    req_carrier = fields.Boolean('Required carrier')


class stock_picking(models.Model):
    _inherit = "stock.picking"

    @api.cr_uid_ids_context
    def do_enter_transfer_details(self, cr, uid, picking, context=None):
        self.check_carrier(cr, uid, picking, context)
        return super(stock_picking, self).do_enter_transfer_details(cr, uid, picking, context)

    @api.cr_uid_ids_context
    def do_transfer(self, cr, uid, picking_ids, context=None):
        self.check_carrier(cr, uid, picking_ids, context)
        return super(stock_picking, self).do_enter_transfer_details(cr, uid, picking_ids, context)

    @api.multi
    def check_carrier(self):
        for picking in self:
            if picking.picking_type_id.req_carrier:
                if not picking.carrier_id:
                    raise Warning(_('Please fill carrier'))
