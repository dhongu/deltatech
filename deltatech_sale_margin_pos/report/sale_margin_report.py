# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class SaleMarginReport(models.Model):
    _inherit = "sale.margin.report"

    pos_order_id = fields.Many2one("pos.order", "POS Order", readonly=True)

    def _select(self):
        return super()._select() + ", pos_order_id"

    def _sub_select(self):
        return super()._sub_select() + ", NULL::integer AS pos_order_id"

    def _extra_sources(self):
        # The orders of the point of sale that were not invoiced; an invoiced order is already in
        # the report through its invoice. The amounts of the order are in the currency of the point
        # of sale, divided by the rate of the order to get the company currency, as in the
        # standard POS reports. total_cost is set when the session is closed (from the stock moves
        # for FIFO/AVCO products); until then the current cost of the product stands in for it.
        cost = """
            CASE WHEN l.is_total_cost_computed
                 THEN l.total_cost / COALESCE(NULLIF(o.currency_rate, 0), 1.0)
                 ELSE l.qty * COALESCE((p.standard_price ->> o.company_id::text)::float, 0)
            END
        """
        columns = {
            "id": "-l.id",
            # date_order is in UTC; the day is the one of the cashier, else an evening sale
            # moves to the next day
            "date": "(o.date_order AT TIME ZONE 'UTC' AT TIME ZONE COALESCE(up.tz, 'UTC'))::date",
            "categ_id": "t.categ_id",
            "product_id": "l.product_id",
            "product_uom": "t.uom_id",
            "product_uom_qty": "l.qty",
            "purchase_price": f"CASE WHEN l.qty = 0 THEN 0 ELSE ({cost}) / l.qty END",
            "sale_val": "l.price_subtotal / COALESCE(NULLIF(o.currency_rate, 0), 1.0)",
            "stock_val": cost,
            "partner_id": "o.partner_id",
            "commercial_partner_id": "rp.commercial_partner_id",
            "state_id": "rp.state_id",
            "company_id": "o.company_id",
            # a paid order: the "Paid" filter and the commission on paid sales take it in
            "payment_state": "'paid'",
            "journal_id": "pc.journal_id",
            "currency_id": "pc.currency_id",
            "user_id": "o.user_id",
            "pos_order_id": "o.id",
        }
        from_str = """
                pos_order_line l
                join pos_order o on (o.id = l.order_id)
                join pos_config pc on (pc.id = o.config_id)
                join product_product p on (p.id = l.product_id)
                join product_template t on (t.id = p.product_tmpl_id)
                left join res_partner rp on (rp.id = o.partner_id)
                left join res_users u on (u.id = o.user_id)
                left join res_partner up on (up.id = u.partner_id)
        """
        source = {
            "from": from_str,
            "where": "o.state in ('paid', 'done') and o.account_move IS NULL",
            "columns": columns,
            # the sales journal of the point of sale: the commission rates of the cashier are set on it
            "user_column": "o.user_id",
            "journal_column": "pc.journal_id",
            "company_column": "o.company_id",
        }
        return super()._extra_sources() + [source]
