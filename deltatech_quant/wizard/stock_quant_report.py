from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp


class StockQuantReport(models.TransientModel):
    _name = 'stock.quant.report'
    _description = "Stock Quant Report"

    location_id = fields.Many2one('stock.location', string='Source Location', required=True)
    refresh_report = fields.Boolean('Refresh Report')
    lines_ids = fields.One2many('stock.quant.report.value', 'report_id')

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
                        pt.description as description,
                        pt.categ_id
                        from stock_quant sq
                            join product_product pp on (sq.product_id=pp.id)
                            join product_template pt on (pp.product_tmpl_id=pt.id)
                        where sq.location_id = %s
                        group by sq.product_id, pt.manufacturer, pt.categ_id, pt.description

            )
        INSERT INTO
            stock_quant_report_value
            (
            report_id,
            create_uid,
            create_date,
            description,
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
            description,
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
        domain = [('location_id', '=', self.location_id.id), ('id', '!=', self.id)]
        if self.refresh_report:
            report = self.env['stock.quant.report'].search(domain)
            report.unlink()
            report = False
        else:
            report = self.env['stock.quant.report'].search(domain, limit=1)

        if not report:
            self.compute_data_for_report()
            report = self

        return report.show_report()


class StockQuantReportValue(models.TransientModel):
    _name = 'stock.quant.report.value'
    _description = "Stock Quant Report"

    report_id = fields.Many2one('stock.quant.report', ondelete='cascade', string='Report')
    product_id = fields.Many2one('product.product', readonly=True, string='Product')

    qty = fields.Float('Quantity', index=True, readonly=True, required=True,
                       help="Quantity of products in this quant, in the default unit of measure of the product")
    product_uom_id = fields.Many2one('product.uom', string='Unit of Measure', related='product_id.uom_id',
                                     readonly=True)

    amount = fields.Float('Stock Amount', readonly=True)

    sale_value = fields.Float('Sale Value', compute='_compute_sale_value', store=True, readonly=True)
    categ_id = fields.Many2one('product.category', string='Internal Category', readonly=True)
    manufacturer = fields.Many2one('res.partner', string='Manufacturer', readonly=True)
    pret_final = fields.Float("Pret final")
    pret_revanzator = fields.Float("Pret revanzator")
    description = fields.Char()

    @api.one
    def _compute_sale_value(self):
        self.sale_value = self.qty * self.product_id.list_price
        price_type = self.env['product.price.type'].search([('field', '=', 'list_price')])
        if price_type:
            sale_currency_id = price_type.currency_id
        else:
            sale_currency_id = self.env.user.company_id
        if 'pricelist_id' in self.env.context:
            pricelist = self.env['product.pricelist'].browse(self.env.context['pricelist_id'])
        else:
            pricelist = self.env['product.pricelist'].browse(6)
        list_currency_id = pricelist.currency_id
        # if 'pricelist_id' in self.env.context:
        #     pricelist = self.env['product.pricelist'].browse(self.env.context['pricelist_id'])
        #     list_currency_id = pricelist.currency_id
        for quant in self:
            quant.pret_final = quant.product_id.list_price
            quant.pret_final_currency_id = sale_currency_id
            if pricelist:
                price = pricelist.price_get(quant.product_id.id, quant.qty)[pricelist.id]
                if price:
                    quant.pret_revanzator = price
                    quant.pret_revanzator_currency_id = list_currency_id
            else:
                quant.pret_revanzator = quant.product_id.list_price
                quant.pret_revanzator_currency_id = sale_currency_id
