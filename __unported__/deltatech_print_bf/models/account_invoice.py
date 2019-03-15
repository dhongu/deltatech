# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details



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
