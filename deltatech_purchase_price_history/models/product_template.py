# ©  2024-now Deltatech
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    min_purchase_price = fields.Float(string="Minimum purchase price")
    max_purchase_price = fields.Float(string="Maximum purchase price")
    avg_purchase_price = fields.Float(string="Average purchase price")

    def compute_purchase_history(self):
        sql = """
        WITH price_stats AS (
            SELECT
                pp.product_tmpl_id,
                MIN(aml.balance/aml.quantity) AS min_price,
                MAX(aml.balance/aml.quantity) AS max_price,
                AVG(aml.balance/aml.quantity) AS avg_price
            FROM
                account_move_line aml
            JOIN
                account_move am ON aml.move_id = am.id
            JOIN
                product_product pp ON aml.product_id = pp.id
            WHERE
                aml.quantity > 0
                AND am.move_type = 'in_invoice'
                AND am.state = 'posted'
                AND am.date >= (CURRENT_DATE - INTERVAL '12 months')
            GROUP BY
                pp.product_tmpl_id
        )
        UPDATE product_template pt
        SET
            min_purchase_price = ps.min_price,
            max_purchase_price = ps.max_price,
            avg_purchase_price = ps.avg_price
        FROM
            price_stats ps
        WHERE
            pt.id = ps.product_tmpl_id;
        """
        self.env.cr.execute(sql)
