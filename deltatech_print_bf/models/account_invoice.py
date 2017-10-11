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


class account_invoice(models.Model):
    _inherit = "account.invoice"



    @api.multi
    def print_bf(self):
         wizard = self.env['account.invoice.export.bf'].with_context({'active_id':self.id}).create({})
         return {
             'type' : 'ir.actions.act_url',
             #'url': '/web/binary/saveas?model=account.invoice.export.bf&field=data_file&id=%s&filename_field=name' % (wizard.id),
             #'url': '/web/content/%s/%s?model=account.invoice.export.bf&field=data_file&filename_field=name' % (wizard.id, wizard.name),
             'url': '/web/binary/download_document?model=account.invoice.export.bf&field=data_file&id=%s&filename=%s' % (wizard.id, wizard.name),
             'target': 'self',
             }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
