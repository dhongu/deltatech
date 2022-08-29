# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import random

from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    sequence_id = fields.Many2one("ir.sequence", string="Code Sequence")
    generate_barcode = fields.Boolean()
    prefix_barcode = fields.Char(default="40", size=2)
    barcode_random = fields.Boolean(default=True)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    _sql_constraints = [
        ("name_code", "unique (default_code,active,company_id)", "Internal Reference already exists !"),
    ]

    @api.model
    def get_new_code(self, categ, default_code, barcode):
        values = {}
        if default_code in [False, "/", "auto"] or self.env.context.get("force_code", False):
            if categ.sequence_id:
                default_code = categ.sequence_id.next_by_id()
                values["default_code"] = default_code

        if not barcode or barcode == "/" or barcode == "auto":
            if categ.generate_barcode:
                if not default_code or categ.barcode_random:
                    default_code = "%0.10d" % random.randint(0, 999999999999)
                barcode = "".join([s for s in default_code if s.isdigit()])
                barcode = categ.prefix_barcode + barcode.zfill(10)
                barcode = self.env["barcode.nomenclature"].sanitize_ean(barcode)
                values["barcode"] = barcode

        return values

    def button_new_code(self):
        for product in self:
            values = self.env["product.template"].get_new_code(product.categ_id, product.default_code, product.barcode)
            product.write(values)
            product.product_variant_ids.write(values)

    # codificare automata  la creare
    @api.model_create_multi
    def create(self, vals_list):
        create_product_product = self.env.context.get("create_product_product", False)
        if not create_product_product:
            for vals in vals_list:
                if "default_code" not in vals or vals["default_code"] in ["/", "", False]:
                    categ_id = vals.get("categ_id")
                    if categ_id:
                        categ = self.env["product.category"].browse(categ_id)
                        default_code = vals.get("default_code", False)
                        barcode = vals.get("barcode", False)
                        values = self.env["product.template"].get_new_code(categ, default_code, barcode)
                        vals.update(values)

        return super(ProductTemplate, self).create(vals_list)

    def force_new_code(self):
        self.with_context(force_code=True).button_new_code()

    @api.model
    def show_not_unique(self):
        sql = """
             SELECT id FROM
              (SELECT *, count(*)
                   OVER   (PARTITION BY  default_code, active) AS count
                    FROM product_template)
               tableWithCount
              WHERE tableWithCount.count > 1;
        """
        self.env.cr.execute(sql)
        product_ids = [x[0] for x in self.env.cr.fetchall()]

        action = self.env.ref("deltatech_product_code.action_force_new_code")
        action.create_action()

        action = self.env.ref("product.product_template_action").read()[0]

        action["domain"] = [("id", "in", product_ids)]
        return action


class ProductProduct(models.Model):
    _inherit = "product.product"

    # la crearea unei variante nu se codifica automat si produsul
    # codificare automata  la creare
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "default_code" not in vals or vals["default_code"] in ["/", "", False]:
                categ_id = vals.get("categ_id")
                if categ_id:
                    categ = self.env["product.category"].browse(categ_id)
                    default_code = vals.get("default_code", False)
                    barcode = vals.get("barcode", False)
                    values = self.env["product.template"].get_new_code(categ, default_code, barcode)
                    vals.update(values)

        return super(ProductProduct, self).create(vals_list)

    def button_new_code(self):
        for product in self:
            values = self.env["product.template"].get_new_code(product.categ_id, product.default_code, product.barcode)
            product.write(values)
