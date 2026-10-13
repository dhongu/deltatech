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
        ],
        ondelete={
            "list_price_bronze": "set default",
            "list_price_copper": "set default",
            "list_price_silver": "set default",
            "list_price_gold": "set default",
        },
    )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    standard_price = fields.Float(tracking=True)
    list_price = fields.Float(tracking=True)

    list_price_base = fields.Selection(
        [
            ("list_price", "List price"),
            ("standard_price", "Cost Price"),
            ("last_purchase_price", "Last Purchase Price"),
        ],
        string="Base Price",
        default="last_purchase_price",
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
        tracking=True,
        store=True,
        readonly=True,
        compute_sudo=True,
    )

    list_price_copper = fields.Float(
        string="Copper Price",
        compute="_compute_price_list",
        tracking=True,
        store=True,
        readonly=True,
        compute_sudo=True,
    )

    list_price_silver = fields.Float(
        string="Silver Price",
        compute="_compute_price_list",
        tracking=True,
        store=True,
        readonly=True,
        compute_sudo=True,
    )
    list_price_gold = fields.Float(
        string="Gold Price",
        compute="_compute_price_list",
        tracking=True,
        store=True,
        readonly=True,
        compute_sudo=True,
    )
    # list_price_platinum = fields.Float(string="Platinum Price", compute="_compute_price_list",
    #                                    tracking=True, store=True, readonly=True, compute_sudo=True)

    price_issue = fields.Boolean(compute="_compute_price_issue", store=True)

    @api.depends(
        "list_price",
        "list_price_copper",
        "list_price_bronze",
        "list_price_silver",
        "list_price_gold",
    )
    def _compute_price_issue(self):
        for product in self:
            product.price_issue = not (
                product.list_price
                >= product.list_price_copper
                >= product.list_price_bronze
                >= product.list_price_silver
                >= product.list_price_gold
            )

    @api.depends(
        "list_price_base",
        "standard_price",
        "last_purchase_price",
        "list_price",
        "percent_copper",
        "percent_bronze",
        "percent_silver",
        "percent_gold",
        "taxes_id",
        "taxes_id.amount",
        "taxes_id.amount_type",
        "taxes_id.include_base_amount",
        "taxes_id.price_include_override",
        "taxes_id.company_id.account_price_include",
        "taxes_id.children_tax_ids",
    )
    def _compute_price_list(self):
        for product in self:
            # de regula este o singura  taxa
            taxe = product.taxes_id.sudo()
            taxe_inc = taxe.flatten_taxes_hierarchy().filtered("price_include")

            if product.list_price_base == "standard_price":
                try:
                    price = product.standard_price
                except Exception:
                    price = product.sudo().standard_price
            elif product.list_price_base == "last_purchase_price":
                price = product.last_purchase_price or product.standard_price
            else:
                price = product.list_price
                if taxe_inc:
                    price = taxe.compute_all(product.list_price)["total_excluded"]

            # pretul de baza este fara taxe; se adauga doar taxele incluse in pret,
            # calculate de motorul de taxe (procent, fix, grup)
            # un produs fara pret de baza ramane cu 0 si cu o taxa fixa
            if taxe_inc and price:
                price = taxe_inc.compute_all(price, handle_price_include=False)["total_included"]
                price = round(price, 2)

            product.list_price_bronze = price * (1 + product.percent_bronze)
            product.list_price_copper = price * (1 + product.percent_copper)
            product.list_price_silver = price * (1 + product.percent_silver)
            product.list_price_gold = price * (1 + product.percent_gold)
            # product.list_price_platinum = price * (1 + product.percent_platinum)

    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1.0,
        uom_id=False,
        only_template=False,
    ):
        combination_info = super()._get_combination_info(combination, product_id, add_qty, uom_id, only_template)

        combination_info["web_list_price"] = combination_info["list_price"]

        return combination_info
