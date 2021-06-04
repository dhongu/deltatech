# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    sequence_id = fields.Many2one("ir.sequence", string="Code Sequence")
    generate_barcode = fields.Boolean()


class ProductTemplate(models.Model):
    _inherit = "product.template"

    default_code = fields.Char(default="/")

    def button_new_code(self):
        self.ensure_one()
        if not self.default_code or self.default_code == "/" or self.default_code == "auto":
            if self.categ_id.sequence_id:
                default_code = self.categ_id.sequence_id.next_by_id()
                self.write({"default_code": default_code})

        if not self.barcode or self.barcode == "/" or self.barcode == "auto":
            if self.categ_id.generate_barcode:
                barcode = "".join([s for s in self.default_code if s.isdigit()])
                barcode = "20" + barcode.zfill(10)
                barcode = self.env["barcode.nomenclature"].sanitize_ean(barcode)
                self.write({"barcode": barcode})


class ProductProduct(models.Model):
    _inherit = "product.product"

    def button_new_code(self):
        for product in self:
            if not product.default_code or product.default_code == "/" or product.default_code == "auto":
                if product.categ_id.sequence_id:
                    default_code = product.categ_id.sequence_id.next_by_id()
                    product.write({"default_code": default_code})

            if not product.barcode or product.barcode == "/" or product.barcode == "auto":
                if product.categ_id.generate_barcode:
                    barcode = "".join([s for s in product.default_code if s.isdigit()])
                    barcode = product.env["barcode.nomenclature"].sanitize_ean(barcode)
                    product.write({"barcode": barcode})
