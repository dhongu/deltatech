# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProductCatalog(models.Model):
    _name = "product.catalog"
    _description = "Extensive Product Catalog"

    name = fields.Char(string="Name", required=True, index=True)
    code = fields.Char(string="Code", required=True, index=True)
    code_new = fields.Char(string="Code New", index=True)
    list_price = fields.Float(string="Sale Price", required=True, digits="Product Price")
    purchase_price = fields.Float(string="Purchase Price", digits="Product Price")
    categ_id = fields.Many2one(
        "product.category", string="Internal Category", required=True, help="Select category for the current product"
    )
    supplier_id = fields.Many2one("res.partner", string="Supplier")
    product_id = fields.Many2one("product.product", string="Product", ondelete="set null")
    purchase_delay = fields.Integer(string="Purchase delay")
    sale_delay = fields.Integer(string="Sale delay")
    list_price_currency_id = fields.Many2one(
        "res.currency", string="Currency List Price", help="Currency for list price."
    )

    _sql_constraints = [
        ("code_uniq", "unique(code)", "Code must be unique !"),
    ]

    def create_product(self):
        prod = self.env["product.product"]
        for prod_cat in self:
            if (not prod_cat.code_new or len(prod_cat.code_new) < 2) and not prod_cat.product_id:

                # route_ids = []
                # mto = self.env.ref("stock.route_warehouse0_mto", raise_if_not_found=False)
                #
                # if mto:
                #     route_ids += [mto.id]
                # buy = self.env.ref("purchase_stock.route_warehouse0_buy", raise_if_not_found=False)
                # if buy:
                #     route_ids += [buy.id]

                currency = self.list_price_currency_id or self.env.user.company_id.currency_id
                list_price = currency._convert(
                    prod_cat.list_price,
                    self.env.user.company_id.currency_id,
                    self.env.user.company_id,
                    fields.Date.today(),
                )

                values = {
                    "name": prod_cat.name,
                    "default_code": prod_cat.code,
                    "lst_price": list_price,
                    "categ_id": prod_cat.categ_id.id,
                    # "route_ids": [(6, 0, route_ids)],
                    "sale_delay": prod_cat.sale_delay,
                }
                if prod_cat.supplier_id:
                    values["seller_ids"] = [
                        (
                            0,
                            0,
                            {
                                "name": prod_cat.supplier_id.id,
                                "price": prod_cat.purchase_price,
                                "currency_id": currency.id,
                                "delay": prod_cat.purchase_delay,
                            },
                        )
                    ]
                old_code = prod_cat.get_echiv()
                if old_code:
                    alt = []
                    for old in old_code:
                        alt.append((0, 0, {"name": old.code}))
                    values["alternative_ids"] = alt

                prod_new = prod.with_context({"no_catalog": True}).search([("default_code", "=ilike", prod_cat.code)])
                if not prod_new:
                    prod_new = prod.sudo().create(values)

                prod_cat.sudo().write({"product_id": prod_new.id})

                prod += prod_new

        return prod

    def get_echiv(self):
        res = self.env["product.catalog"]
        for prod_cat in self:
            ids_old = self.search([("code_new", "=ilike", prod_cat.code)])
            if ids_old:
                ids_very_old = ids_old.get_echiv()
                res = ids_old | ids_very_old
            else:
                res = ids_old
        return res

    @api.model
    def search_in_catalog(self, name):
        alt = []
        prod_cat = self.env["product.catalog"]
        res = None
        while name and len(name) > 2:
            prod_cat = self.env["product.catalog"].search([("code", "=ilike", name)], limit=1)
            if prod_cat:
                alt.append(name)
                name = prod_cat.code_new  # codul cu care a fost inlocuit
            else:
                name = ""
        if prod_cat:
            if not prod_cat.product_id:
                prod_new = prod_cat.create_product()
                res = prod_new
            else:
                res = prod_cat.product_id
        return res
