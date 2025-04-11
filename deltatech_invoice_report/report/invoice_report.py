# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    state_id = fields.Many2one("res.country.state", string="Region", readonly=True)
    supplier_id = fields.Many2one("res.partner", string="Default Supplier", readonly=True)
    product_tmpl_id = fields.Many2one("product.template", string="Product Template", readonly=True)

    def _select(self) -> SQL:
        return SQL(
            "%s , partner.state_id,   supplier.partner_id as supplier_id, template.id as product_tmpl_id",
            super()._select(),
        )

    def _from(self) -> SQL:
        return SQL(
            "%s LEFT JOIN ( select product_tmpl_id, min(partner_id) as partner_id from product_supplierinfo group by product_tmpl_id ) supplier ON template.id = supplier.product_tmpl_id",
            super()._from(),
        )

        # return (
        #     super()._from()
        #     + """
        #  LEFT JOIN ( select product_tmpl_id, min(partner_id) as partner_id
        #  from product_supplierinfo group by product_tmpl_id ) supplier ON template.id = supplier.product_tmpl_id
        # """
        # )

    def _group_by(self):
        return super()._group_by() + ", partner.state_id,     supplier.partner_id "
