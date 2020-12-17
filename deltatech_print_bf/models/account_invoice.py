# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models
from odoo.tools.translate import _


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def print_bf(self):
        wizard = self.env["account.invoice.export.bf"].with_context({"active_id": self.id}).create({})

        message = _("Fisier Bon Fiscal  %s generat") % wizard.name
        self.message_post(body=message)
        wizard_download = self.env["wizard.download.file"].create(
            {"data_file": wizard.data_file, "file_name": wizard.name}
        )

        return wizard_download.do_download_file()


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def default_get(self, fields):
        defaults = super(SaleOrder, self).default_get(fields)
        is_bf = self.env.context.get("is_bf", False)
        if is_bf:
            defaults["partner_id"] = self.env.ref("deltatech_partner_generic.partner_generic").id
        return defaults
