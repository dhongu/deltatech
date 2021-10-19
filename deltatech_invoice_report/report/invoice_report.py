# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    state_id = fields.Many2one("res.country.state", string="Region", readonly=True)
    supplier_id = fields.Many2one("res.partner", string="Default Supplier", readonly=True)

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + ", partner.state_id,   supplier.name as supplier_id"

    def _from(self):
        return (
            super(AccountInvoiceReport, self)._from()
            + """
         LEFT JOIN ( select product_tmpl_id, min(name) as name
         from product_supplierinfo group by product_tmpl_id ) supplier ON template.id = supplier.product_tmpl_id
        """
        )

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ", partner.state_id,     supplier.name "
