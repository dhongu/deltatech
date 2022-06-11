# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection(
        selection_add=[
            ("list_price_bronze", "Bronze Price"),
            ("list_price_copper", "Copper Price"),
            ("list_price_silver", "Silver Price"),
            ("list_price_gold", "Gold Price"),
            #    ('list_price_platinum', 'Platinum Price'),
        ]
    )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    standard_price = fields.Float(track_visibility="always")
    list_price = fields.Float(track_visibility="always")

    list_price_base = fields.Selection(
        [("list_price", "List price"), ("standard_price", "Cost Price")], string="Base Price", default="standard_price"
    )

    percent_bronze = fields.Float(string="Bronze Percent")
    percent_copper = fields.Float(string="Copper Percent")
    percent_silver = fields.Float(string="Silver Percent")
    percent_gold = fields.Float(string="Gold Percent")
    # percent_platinum = fields.Float(string="Platinum Percent")

    # todo: de adus valorile din listele de preturi
    list_price_bronze = fields.Float(
        string="Bronze Price",
        compute="_compute_price_list",
        track_visibility="always",
        store=True,
        readonly=True,
        compute_sudo=True,
    )

    list_price_copper = fields.Float(
        string="Copper Price",
        compute="_compute_price_list",
        track_visibility="always",
        store=True,
        readonly=True,
        compute_sudo=True,
    )

    list_price_silver = fields.Float(
        string="Silver Price",
        compute="_compute_price_list",
        track_visibility="always",
        store=True,
        readonly=True,
        compute_sudo=True,
    )
    list_price_gold = fields.Float(
        string="Gold Price",
        compute="_compute_price_list",
        track_visibility="always",
        store=True,
        readonly=True,
        compute_sudo=True,
    )
    # list_price_platinum = fields.Float(string="Platinum Price", compute="_compute_price_list",
    #                                    track_visibility='always', store=True, readonly=True, compute_sudo=True)

    price_issue = fields.Boolean(compute="_compute_price_issue", store=True)

    @api.multi
    @api.depends("list_price", "list_price_copper", "list_price_bronze", "list_price_silver", "list_price_gold")
    def _compute_price_issue(self):
        for product in self:
            product.price_issue = not (
                product.list_price
                >= product.list_price_copper
                >= product.list_price_bronze
                >= product.list_price_silver
                >= product.list_price_gold
            )

    @api.multi
    @api.depends(
        "list_price_base",
        "standard_price",
        "list_price",
        "percent_copper",
        "percent_bronze",
        "percent_silver",
        "percent_gold",
        "taxes_id",
    )
    def _compute_price_list(self):

        for product in self:
            tax_inc = False
            # de regula este o singura  taxa
            taxe = product.taxes_id.sudo()

            for tax in taxe:
                if tax.price_include:
                    tax_inc = True

            # se presupune ca pretul de achizitie este cu taxa inclusa
            if product.list_price_base == "standard_price":
                try:
                    price = product.standard_price
                except Exception:
                    price = product.sudo().standard_price
                # taxe = taxe.with_context(base_values=price)
            else:
                price = product.list_price
                if tax_inc:
                    taxes = taxe.compute_all(product.list_price)
                    price = taxes["total_excluded"]

            if tax_inc:
                tax_value = 0.0
                for tax in taxe.sorted(key=lambda r: r.sequence):
                    tax_value += price * tax.amount / 100
                price += tax_value
                price = round(price, 2)

            product.list_price_bronze = price * (1 + product.percent_bronze)
            product.list_price_copper = price * (1 + product.percent_copper)
            product.list_price_silver = price * (1 + product.percent_silver)
            product.list_price_gold = price * (1 + product.percent_gold)
            # product.list_price_platinum = price * (1 + product.percent_platinum)

    @api.multi
    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1,
        pricelist=False,
        parent_combination=False,
        only_template=False,
    ):

        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            pricelist=pricelist,
            parent_combination=parent_combination,
            only_template=only_template,
        )

        combination_info["web_list_price"] = combination_info["list_price"]

        return combination_info
