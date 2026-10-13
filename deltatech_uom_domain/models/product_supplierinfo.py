# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProductSupplierinfo(models.Model):
    _name = "product.supplierinfo"
    _inherit = ["product.supplierinfo", "deltatech.uom.domain.mixin"]

    allowed_uom_ids = fields.Many2many("uom.uom", compute="_compute_allowed_uom_ids")
    product_uom_id = fields.Many2one(domain="[('id', 'in', allowed_uom_ids)]")

    @api.depends("product_id.uom_id", "product_id.uom_ids", "product_tmpl_id.uom_id", "product_tmpl_id.uom_ids")
    def _compute_allowed_uom_ids(self):
        """Pe linia de furnizor standardul nu pune niciun domeniu pe UM.

        In 19.0 `uom.uom._compute_quantity()` nu mai verifica compatibilitatea, asa ca
        o unitate din alt arbore trece fara eroare: "ml" (mililitru) ales pentru un
        produs in metri transforma 22,5 m in 22.500 ml pe cererea de oferta. Aici se
        ofera doar UM produsului, `uom_ids` si unitatile din acelasi arbore.
        """
        for record in self:
            product = record.product_id or record.product_tmpl_id
            record.allowed_uom_ids = product.uom_id | product.uom_ids
        self._extend_allowed_uom_ids()

    def _uom_domain_product_uom(self):
        """Linia de furnizor poate fi pe sablon, fara varianta."""
        self.ensure_one()
        return (self.product_id or self.product_tmpl_id).uom_id
