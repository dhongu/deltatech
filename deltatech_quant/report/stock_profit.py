# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools


class StockProfitReport(models.Model):
    _name = "stock.profit.report"
    _description = "Stock Statistics"
    _auto = False

    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_qty = fields.Float(string='Product Quantity', readonly=True)
    location_id = fields.Many2one('stock.location', 'Location', readonly=True)

    categ_id = fields.Many2one('product.category', 'Category', readonly=True)

    input_qty = fields.Float(string='Input Quantity', readonly=True)
    input_date = fields.Date(string='Input date', readonly=True)
    input_amount = fields.Float(string="Input Amount", readonly=True)

    output_qty = fields.Float(string='Output Quantity', readonly=True)
    output_date = fields.Date(string='Output date', readonly=True)

    output_amount = fields.Float(string="Output Amount", readonly=True)

    customer_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier', readonly=True)
    manufacturer = fields.Many2one('res.partner', string='Manufacturer', readonly=True)

    profit = fields.Float(string="Profit", readonly=True)

    sale_value = fields.Float('Sale Value',  readonly=True)

    qty_available = fields.Float(string='Quantity On Hand')


    @api.multi
    def _compute_quantities(self):
        for item in self:
            self.qty_available = item.product_id.with_context(location=self.location_id)._qty_available



    def _select(self):
        select_str = """
            id, product_id, qty_available, categ_id, product_qty, location_id,
             input_qty, input_date, input_amount,
             output_qty, output_date,  output_amount, sale_value,
             customer_id,  supplier_id, 
             manufacturer, profit
        """
        return select_str

    def _sub_select(self):
        select_str = """
        max(sq.id) as id, sum(available.qty_available) as qty_available,
        sq.product_id,  pt.categ_id, sq.location_id, sq.input_date, sq.output_date,

        SUM( sq.qty ) as product_qty,

        SUM(CASE
            WHEN sq.input_date is not null
                THEN sq.qty
                ELSE 0
            END) AS input_qty,

        SUM(CASE
            WHEN sl.usage = 'customer'
                THEN sq.qty
                ELSE 0
            END) AS output_qty,

        sum(sq.input_amount) as input_amount,
        sum(sq.output_amount) as output_amount,
        sum(sq.qty * pt.list_price) as sale_value,
        sq.customer_id,
        sq.supplier_id,
        pt.manufacturer,
        SUM(CASE
            WHEN sl.usage = 'customer'
                THEN sq.output_amount-sq.input_amount
                ELSE 0
            END) AS profit

        """
        return select_str

    def _from(self):
        from_str = """
         stock_quant as sq
            join stock_location as sl on sq.location_id = sl.id
            join product_product pp on (sq.product_id=pp.id)
            join product_template pt on (pp.product_tmpl_id=pt.id)
            left join ( 
                    select sum(qty) as qty_available , stock_quant.product_id, stock_quant.location_id,
                                   supplier_id
                        from stock_quant 
                                join stock_location on stock_location.id = stock_quant.location_id
                         where stock_location.usage =  'internal'
                          group by stock_quant.product_id, stock_quant.location_id,   supplier_id
                          
            ) available on available.product_id = sq.product_id and 
                           available.location_id = sq.location_id and 
                           available.supplier_id = sq.supplier_id
        """
        return from_str

    def _where(self):
        where_str = """
            sl.usage =  'internal' or sl.usage = 'customer'
        """
        return where_str

    def _group_by(self):
        group_by_str = """
            sq.product_id, pt.categ_id, sq.location_id,   sq.input_date, sq.output_date,
            sq.customer_id, sq.supplier_id, pt.manufacturer
        """
        return group_by_str

    @api.model_cr
    def init(self):
        # self._table = account_invoice_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT %s
            FROM (
                SELECT %s
                FROM %s
                WHERE %s
                GROUP BY %s
            ) AS sub

        )""" % (self._table, self._select(), self._sub_select(),
                self._from(), self._where(), self._group_by()))
