# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class VendorInfo(models.Model):
    _name = "vendor.info"
    _description = "Vendor Info"

    name = fields.Char(string="Name", required=True, index=True)
    supplier_id = fields.Many2one("res.partner", string="Supplier", index=True)
    currency_id = fields.Many2one("res.currency", string="Currency", index=True)
    sequence_id = fields.Many2one("ir.sequence", string="Code Sequence")
    purchase_delay = fields.Integer(default=2)
    type_code = fields.Selection([("none", "None"), ("sequence", "Sequence"), ("code", "Code")], default="none")
    category_id = fields.Many2one("product.category", string="Product Category")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company, required=True)

    @api.onchange("supplier_id")
    def onchange_supplier_id(self):
        if self.supplier_id:
            self.currency_id = self.supplier_id.property_purchase_currency_id
            self.name = self.supplier_id.name

    def load_from_file(self):
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_vendor_products.product_template_action")
        return action

    def unlink_product(self):
        self.env["vendor.product"].search([("supplier_id", "=", self.supplier_id.id)]).unlink()
