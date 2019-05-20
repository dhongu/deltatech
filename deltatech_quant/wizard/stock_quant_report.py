


from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp


class StockQuantReport(models.TransientModel):
    _name = 'stock.quant.report'
    _description = "Stock Quant Report"

    location_id = fields.Many2one(  'stock.location', 'Source Location', required=True )
    lines_ids = fields.One2many('stock.quant.report.value','report_id')

    @api.multi
    def compute_data_for_report(self):
        self.ensure_one()


        query_inject = '''
        WITH
            q AS (
                    SELECT  
                        sq.product_id, 
                        sum(sq.qty) as qty, 
                        sum(coalesce(sq.cost*sq.qty,0.0)) as amount,
                        sum(coalesce(pt.list_price*sq.qty,0.0)) as sale_value,
                        pt.manufacturer,
                        pt.categ_id
                        from stock_quant sq
                            join product_product pp on (sq.product_id=pp.id)
                            join product_template pt on (pp.product_tmpl_id=pt.id)
                        where sq.location_id = %s
                        group by sq.product_id, pt.manufacturer, pt.categ_id

            )
        INSERT INTO
            stock_quant_report_value
            (
            report_id,
            create_uid,
            create_date,
            
            product_id,
            qty,
            amount,
            sale_value,
            manufacturer,
            categ_id
            
            )
        SELECT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
        
            product_id,
            qty,
            amount,
            sale_value,
            manufacturer,
            categ_id
        FROM
            q
        
                '''
        query_inject_params = (self.location_id.id, self.id, self.env.uid)
        self.env.cr.execute(query_inject, query_inject_params)
        self.refresh()
        self.lines_ids.refresh()
        self.lines_ids._compute_sale_value()


    def show_report(self):
        self.ensure_one()
        action = self.env.ref('deltatech_quant.action_stock_quant_report_value')
        vals = action.read()[0]
        vals['domain'] = [('report_id', '=', self.id)]
        return vals

    @api.multi
    def do_execute(self):
        self.compute_data_for_report()

        return self.show_report()


class StockQuantReportValue(models.TransientModel):
    _name = 'stock.quant.report.value'
    _description = "Stock Quant Report"

    report_id = fields.Many2one('stock.quant.report', ondelete='cascade',)
    product_id = fields.Many2one('product.product' , readonly=True)

    qty = fields.Float(  'Quantity', index=True, readonly=True, required=True,
        help="Quantity of products in this quant, in the default unit of measure of the product")
    product_uom_id = fields.Many2one( 'product.uom', string='Unit of Measure', related='product_id.uom_id', readonly=True)

    amount = fields.Float('Amount', readonly=True)
    sale_value = fields.Float('Sale Value', compute='_compute_sale_value', store=True, readonly=True)
    categ_id = fields.Many2one('product.category', string='Internal Category',  readonly=True)
    manufacturer = fields.Many2one('res.partner', string='Manufacturer',   readonly=True)

    @api.one
    def _compute_sale_value(self):
        self.sale_value = self.qty * self.product_id.list_price