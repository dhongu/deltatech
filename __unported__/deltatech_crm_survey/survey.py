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



from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp


class survey_user_input(models.Model):
    _inherit = "survey.user_input"
    
    lead_id = fields.Many2one('crm.lead', string='Lead')

    @api.multi
    def write(self, vals):
        if 'state' in vals:
            user_input = self.sudo()
            if vals['state'] == 'done' and user_input.lead_id :
                msg = _('Survey %s was done') % user_input.survey_id.title
                message_id = user_input.lead_id.message_post(body=msg)
                message = self.env['mail.message'].browse(message_id)
                message.set_message_read( read=False )
        res = super(survey_user_input, self).write(vals) 

        return res

 


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
