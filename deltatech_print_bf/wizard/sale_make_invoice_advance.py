# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError

import odoo.addons.decimal_precision as dp

# mapping invoice type to journal type


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.model
    def default_get(self, fields_list):
        defaults = super(SaleAdvancePaymentInv, self).default_get(fields_list)

        if self._context.get("default_journal_id", False):
            return self.env["account.journal"].browse(self._context.get("default_journal_id"))

        if self._context.get("active_ids"):
            company_id = self._context.get("company_id", self.env.user.company_id.id)
            sale_obj = self.env["sale.order"]
            order = sale_obj.browse(self._context.get("active_ids"))[0]

            generic_parnter_id = self.env["ir.config_parameter"].sudo().get_param("sale.partner_generic_id")
            generic_parnter = self.env["res.partner"].browse(int(generic_parnter_id)).exists()
            if generic_parnter == order.partner_id:
                journal_bf_id = self.env["ir.config_parameter"].sudo().get_param("sale.journal_bf_id")
                journal_bf = self.env["account.journal"].browse(int(journal_bf_id)).exists()
                if journal_bf:
                    defaults["journal_id"] = journal_bf.id

            # generic_parnter = self.env.ref('deltatech_partner_generic.partner_generic',raise_if_not_found=False)
            # if generic_parnter == order.partner_id:
            #     domain = [
            #         ('type', '=', 'sale'),
            #         ('company_id', '=', company_id),
            #         ('code', '=', 'BF')
            #     ]
            # else:
            #     domain = [
            #         ('type', '=', 'sale'),
            #         ('company_id', '=', company_id),
            #         ('code', '!=', 'BF')
            # ]
            # journal  = self.env['account.journal'].search(domain, limit=1)
            # if journal:
            #     defaults['journal_id'] = journal.id

        return defaults

    # @api.model
    # def _default_journal(self):
    #
    #     if self._context.get('default_journal_id', False):
    #         return self.env['account.journal'].browse(self._context.get('default_journal_id'))
    #
    #     if not self._context.get('active_ids'):
    #         return False
    #
    #
    #     company_id = self._context.get('company_id', self.env.user.company_id.id)
    #
    #
    #     sale_obj = self.env['sale.order']
    #     order = sale_obj.browse(self._context.get('active_ids'))[0]
    #
    #     generic_parnter = self.env.ref('deltatech_partner_generic.partner_generic',raise_if_not_found=False)
    #     if generic_parnter == order.partner_id:
    #         domain = [
    #             ('type', '=', 'sale'),
    #             ('company_id', '=', company_id),
    #             ('code', '=', 'BF')
    #         ]
    #     else:
    #         domain = [
    #             ('type', '=', 'sale'),
    #             ('company_id', '=', company_id),
    #             ('code', '!=', 'BF')
    #         ]
    #
    #
    #     return self.env['account.journal'].search(domain, limit=1)
    #
    #
    # journal_id = fields.Many2one('account.journal', string='Journal',
    #                              default=_default_journal,
    #                              domain="[('type', '=', 'sale')]") # de adaugat si ('company_id', '=', company_id)

    # @api.multi
    # def create_invoices(self):
    #     new_self = self.with_context(default_journal_id=self.journal_id)
    #     return super(SaleAdvancePaymentInv, new_self).create_invoices()
