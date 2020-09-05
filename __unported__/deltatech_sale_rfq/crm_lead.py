# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import logging
from odoo.osv.fields import related

_logger = logging.getLogger(__name__)


class crm_lead(models.Model):
    _inherit = 'crm.lead'

    @api.multi
    def button_rfq(self):
        self.ensure_one()
        if not self.partner_id:
            raise Warning('Customer not found')

        rfq = self.env['sale.rfq'].search([('lead_id', '=', self.id)])

        if not rfq:
            rfq = self.env['sale.rfq'].create({'lead_id': self.id, 'team_leader_id': self.section_id.user_id.id})

        action = {
            'domain': str([('id', 'in', rfq.ids)]),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.rfq',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'name': _('Request for Quotation'),
            'res_id': rfq.ids[0]
        }
        if len(rfq) > 1:
            action['view_mode'] = 'tree,form'
        return action

    @api.model
    def merge_dependences(self, highest, opportunities):
        print highest, opportunities
        res = super(crm_lead, self).merge_dependences(highest, opportunities)
        self._merge_opportunity_rfq(highest, opportunities)
        return res

    @api.model
    def _merge_opportunity_rfq(self, opportunity_id, opportunities):

        for opportunity in opportunities:
            rfq = self.env['sale.rfq'].search([('lead_id', '=', opportunity.id)])
            if rfq:
                rfq.write({'lead_id': opportunity_id})
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
