# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models, tools


class DeltatechSaleReport(models.Model):
    _name = "deltatech.sale.report"
    _description = "Deltatech sale report"
    _auto = False

    date = fields.Datetime("Date", readonly=True)
    categ_id = fields.Many2one("product.category", "Category", readonly=True)
    product_id = fields.Many2one("product.product", "Product", readonly=True)
    product_uom = fields.Many2one("uom.uom", "Unit of Measure", readonly=True)
    product_uom_qty = fields.Float("Quantity", readonly=True)
    sale_val = fields.Float("Sale value", readonly=True)

    stock_val = fields.Float(string="Stock value", readonly=True)
    profit_val = fields.Float(string="Profit", readonly=True)

    partner_id = fields.Many2one("res.partner", "Partner", readonly=True)
    user_id = fields.Many2one("res.users", "Salesperson", readonly=True)
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse", required=True)
    company_id = fields.Many2one("res.company", "Company", readonly=True)
    nbr = fields.Integer("# of Lines", readonly=True)
    state = fields.Selection(
        [
            ("draft", "Quotation"),
            ("sent", "Quotation Sent"),
            ("sale", "Sales Order"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ],
        "Order Status",
        readonly=True,
    )
    pricelist_id = fields.Many2one("product.pricelist", "Pricelist", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, "deltatech_sale_report")
        self.env.cr.execute(
            """

            create or replace view deltatech_sale_report as (
             select *,  sale_val - stock_val as profit_val
            from (
                select
                    l.id as id,
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
                    sum(l.product_uom_qty / u.factor * u2.factor) * l.purchase_price  as stock_val,
                    s.pricelist_id as pricelist_id


                from
                    sale_order s
                    left join sale_order_line l on (s.id=l.order_id)
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join uom_uom u on (u.id=l.product_uom)
                    left join uom_uom u2 on (u2.id=t.uom_id)



                group by
                    l.id,
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

       ) as sub) """
        )
