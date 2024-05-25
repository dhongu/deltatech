# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    state_id = fields.Many2one("res.country.state", string="Region", readonly=True)
    supplier_id = fields.Many2one("res.partner", string="Default Supplier", readonly=True)
    product_tmpl_id = fields.Many2one("product.template", string="Product Template", readonly=True)

    def _select(self):
        return super()._select() + ", partner.state_id,   supplier.name as supplier_id, template.id as product_tmpl_id"

    def _from(self):
        return (
            super()._from()
            + """
         LEFT JOIN ( select product_tmpl_id, min(name) as name
         from product_supplierinfo group by product_tmpl_id ) supplier ON template.id = supplier.product_tmpl_id
        """
        )

    def _group_by(self):
        return super()._group_by() + ", partner.state_id,     supplier.name, template.id "
