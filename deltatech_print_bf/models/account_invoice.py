# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
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

         message = (_("Fisier Bon Fiscal  %s generat") % ( wizard.name))
         self.message_post(body=message)
         wizard_download = self.env['wizard.download.file'].create({'data_file': wizard.data_file, 'file_name': wizard.name})

         return wizard_download.do_download_file()

         # return {
         #     'type' : 'ir.actions.act_url',
         #     #'url': '/web/binary/saveas?model=account.invoice.export.bf&field=data_file&id=%s&filename_field=name' % (wizard.id),
         #     #'url': '/web/content/%s/%s?model=account.invoice.export.bf&field=data_file&filename_field=name' % (wizard.id, wizard.name),
         #     'url': '/web/binary/download_document?model=account.invoice.export.bf&field=data_file&id=%s&filename=%s' % (wizard.id, wizard.name),
         #     'target': 'self',
         #     }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def default_get(self, fields):
        defaults = super(SaleOrder, self).default_get(fields)
        is_bf = self.env.context.get('is_bf', False)
        if is_bf:
            defaults['partner_id'] = 4434
        return defaults
        