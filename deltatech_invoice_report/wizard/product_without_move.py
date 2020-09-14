# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

import odoo.addons.decimal_precision as dp


class ProductWithoutMove(models.TransientModel):
    _name = "product.without.move"
    _description = "Product Without Move"

    date_from = fields.Date(string="Start Date", required=True, default=fields.Date.today)
    date_to = fields.Date(string="End Date", required=True, default=fields.Date.today)

    item_ids = fields.One2many("product.without.move.item", "report_id")

    @api.model
    def default_get(self, fields_list):
        res = super(ProductWithoutMove, self).default_get(fields_list)
        today = fields.Date.context_today(self)

        from_date = today + relativedelta(day=1, month=1, years=-5)
        to_date = today

        res["date_from"] = from_date
        res["date_to"] = to_date
        return res

    @api.multi
    def do_show_report(self):
        active_model = self.env.context.get("active_model", False)
        active_ids = self.env.context.get("active_ids", False)
        if active_model == "product.template":
            products = self.env["product.product"].search([("product_tmpl_id", "in", active_ids)])
        elif active_model == "product.product":
            products = self.env["product.product"].browse(active_ids)

        sql = """

            select %s as report_id , product_id, max(date_invoice) as last_sale_date,
             current_date-max(date_invoice) as days_last_sale
            from account_invoice_line as l
                join account_invoice as i on i.id = l.invoice_id
            where product_id in %s
            group by product_id
        """

        if len(products) == 1:
            self.env.cr.execute(sql, (self.id, "(%s)" % products.id))
        else:
            self.env.cr.execute(sql, (self.id, tuple(products.ids)))

        query_results = self.env.cr.dictfetchall()

        self.env["product.without.move.item"].create(query_results)

        for product in products:
            domain = [("report_id", "=", self.id), ("product_id", "=", product.id)]
            item = self.env["product.without.move.item"].search(domain)
            if item:
                item.write(
                    {
                        "qty": product.qty_available,
                        "price": product.standard_price,
                        "amount": product.qty_available * product.standard_price
                        # todo: de determinat pretul din miscarile de stoc
                    }
                )
            else:
                if product.qty_available != 0:
                    self.env["product.without.move.item"].create(
                        {
                            "report_id": self.id,
                            "product_id": product.id,
                            "qty": product.qty_available,
                            "days_last_sale": "9999",
                            "price": product.standard_price,
                            "amount": product.qty_available * product.standard_price,
                        }
                    )

        action = {
            "name": _("Products without move"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree",
            "context": {"active_id": self.id},
            "res_model": "product.without.move.item",
            "domain": [("report_id", "=", self.id)],
        }
        return action


class ProductWithoutMoveItem(models.TransientModel):
    _name = "product.without.move.item"
    _description = "Product Without Move Item"
    _rec_name = "product_id"

    report_id = fields.Many2one("product.without.move")
    product_id = fields.Many2one("product.product", string="Product")
    qty = fields.Float(string="Quantity", digits=dp.get_precision("Product Unit of Measure"))
    last_sale_date = fields.Date(string="Last Sale Date")
    days_last_sale = fields.Integer("Days from last sale")
    amount = fields.Float(digits=dp.get_precision("Account"), string="Amount")
    price = fields.Float(digits=dp.get_precision("Product Price"), string="Price")
