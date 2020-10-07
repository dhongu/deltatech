# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models, tools


class DeltatechSaleReport(models.Model):
    _name = "deltatech.sale.report"
    _description = "Deltatech sale report"
    _auto = False

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):

        res = super(DeltatechSaleReport, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )

        prod_dict = {}
        if "stock_val" in fields or "profit_val" in fields:
            for line in res:
                lines = self.search(line.get("__domain", []))
                inv_value = 0.0
                sale_val = 0.0
                # product_tmpl_obj = self.pool.get("product.template")

                for line_rec in lines:
                    if line_rec.product_id.cost_method == "real":
                        # price = line_rec.price_unit_on_quant
                        # trbuie sa determin care este miscare cu care a fost facuta iesire din
                        # stoc si de acolo sa gasesc care e quntul din care sa citesc pretul!!! fack!
                        if line_rec.product_id.id not in prod_dict:
                            prod_dict[line_rec.product_id.id] = line_rec.product_id.get_history_price(
                                line_rec.company_id.id, date=line_rec.date
                            )
                        price = prod_dict[line_rec.product_id.id] or line_rec.product_id.standard_price
                    else:
                        if line_rec.product_id.id not in prod_dict:
                            prod_dict[line_rec.product_id.id] = line_rec.product_id.get_history_price(
                                line_rec.company_id.id, date=line_rec.date
                            )
                        price = prod_dict[line_rec.product_id.id] or line_rec.product_id.standard_price
                    inv_value += price * line_rec.product_uom_qty
                    sale_val += line_rec.sale_val
                line["stock_val"] = inv_value
                line["profit_val"] = sale_val - inv_value
        return res

    date = fields.Datetime("Date", size=6, readonly=True)
    categ_id = fields.Many2one("product.category", "Category", readonly=True)
    product_id = fields.Many2one("product.product", "Product", readonly=True)
    product_uom = fields.Many2one("uom.uom", "Unit of Measure", readonly=True)
    product_uom_qty = fields.Float("Quantity", readonly=True)
    sale_val = fields.Float("Sale value", readonly=True)

    stock_val = fields.Float(string="Stock value", readonly=True, computed="_get_stock_val", store=True)
    profit_val = fields.Float(string="Profit", readonly=True, computed="_get_profit_val", store=True)
    partner_id = fields.Many2one("res.partner", "Partner", readonly=True)
    user_id = fields.Many2one("res.users", "Salesperson", readonly=True)
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse", required=True)
    company_id = fields.Many2one("res.company", "Company", readonly=True)
    nbr = fields.Integer("# of Lines", readonly=True)
    state = fields.Selection(
        [
            ("draft", "Quotation"),
            ("waiting_date", "Waiting Schedule"),
            ("manual", "Manual In Progress"),
            ("progress", "In Progress"),
            ("invoice_except", "Invoice Exception"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        "Order Status",
        readonly=True,
    )
    pricelist_id = fields.Many2one("product.pricelist", "Pricelist", readonly=True)

    def _get_stock_val(self):
        for line in self:
            price_unit = line.product_id.product_tmpl_id.get_history_price(line.company_id.id, date=line.date)
            line.stock_val = line.product_uom_qty * price_unit

    def _get_profit_val(self):
        for line in self:
            line.profit_val = line.sale_val - line.stock_val

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, "deltatech_sale_report")
        self.env.cr.execute(
            """

         create or replace view deltatech_sale_report as (
                select
                    min(l.id) as id,
                    s.date_order as date,
                    t.categ_id as categ_id,
                    l.product_id as product_id,
                    t.uom_id as product_uom,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.product_uom_qty * l.price_unit * (100.0-l.discount) / 100.0) as sale_val,

                    count(*)  as nbr,

                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.warehouse_id as warehouse_id,
                    s.company_id as company_id,

                    s.state,

                    s.pricelist_id as pricelist_id,
                    0 as stock_val,
                    0 as profit_val

                from
                    sale_order s
                    left join sale_order_line l on (s.id=l.order_id)
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join uom_uom u on (u.id=l.product_uom)
                    left join uom_uom u2 on (u2.id=t.uom_id)



                group by
                    l.product_id,
                    l.product_uom_qty,
                    l.order_id,
                    t.uom_id,
                    t.categ_id,
                    s.date_order,

                    s.partner_id,
                    s.user_id,
                    s.warehouse_id,
                    s.company_id,
                    s.state,
                    s.pricelist_id

       ) """
        )
