# Copyright (C) 2020 NextERP Romania
# Copyright (C) 2020 Terrabit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

import pytz

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StorageSheet(models.TransientModel):
    _inherit = "l10n.ro.stock.storage.sheet"

    only_active = fields.Boolean(default=False)

    def do_compute_product(self):
        if not self.only_active:
            return super().do_compute_product()
        else:
            if self.product_ids:
                product_list = self.product_ids.ids
                all_products = False
            else:
                if self.products_with_move:
                    product_list = self.get_products_with_move_sql()
                    all_products = False
                    if not product_list:
                        raise UserError(_("There are no stock movements in the selected period"))
                else:
                    product_list = [-1]  # dummy list
                    all_products = True

            self.env["account.move.line"].check_access_rights("read")

            lines = self.env["l10n.ro.stock.storage.sheet.line"].search([("report_id", "=", self.id)])
            lines.unlink()

            datetime_from = fields.Datetime.to_datetime(self.date_from)
            datetime_from = fields.Datetime.context_timestamp(self, datetime_from)
            datetime_from = datetime_from.replace(hour=0)
            datetime_from = datetime_from.astimezone(pytz.utc)

            datetime_to = fields.Datetime.to_datetime(self.date_to)
            datetime_to = fields.Datetime.context_timestamp(self, datetime_to)
            datetime_to = datetime_to.replace(hour=23, minute=59, second=59)
            datetime_to = datetime_to.astimezone(pytz.utc)

            if self.detailed_locations:
                all_locations = self.with_context(active_test=False).location_ids
            else:
                all_locations = self.location_id
                locations = self.location_ids

            for location in all_locations:
                if self.detailed_locations:
                    locations = location
                params = {
                    "report": self.id,
                    "location": location.id,
                    "locations": tuple(locations.ids),
                    "product": tuple(product_list),
                    "all_products": all_products,
                    "company": self.company_id.id,
                    "date_from": fields.Date.to_string(self.date_from),
                    "date_to": fields.Date.to_string(self.date_to),
                    "datetime_from": fields.Datetime.to_string(datetime_from),
                    "datetime_to": fields.Datetime.to_string(datetime_to),
                    "tz": self._context.get("tz") or self.env.user.tz or "UTC",
                }
                _logger.info("start query_select_sold_init %s", location.name)
                query_select_sold_init = """
                 insert into l10n_ro_stock_storage_sheet_line
                  (report_id, product_id, amount_initial, quantity_initial, unit_price_in,
                   account_id, date_time, date, reference, document, location_id  )

                select * from(
                    SELECT %(report)s as report_id, prod.id as product_id,
                        COALESCE(sum(svl.value), 0)  as amount_initial,
                        COALESCE(sum(svl.quantity), 0)  as quantity_initial,
                        CASE
                            WHEN ROUND(COALESCE(sum(svl.quantity), 0), 5) != 0
                                THEN ROUND(COALESCE(sum(svl.value),0) / sum(svl.quantity), 2)
                            ELSE 0
                        END as unit_price_in,
                        COALESCE(svl.l10n_ro_account_id, Null) as account_id,
                        %(datetime_from)s::timestamp without time zone  as date_time,
                        %(date_from)s::date as date,
                        %(reference)s as reference,
                        %(reference)s as document,
                        %(location)s as location_id
                    from product_product as prod
                    join stock_move as sm ON sm.product_id = prod.id AND sm.state = 'done' AND
                        sm.company_id = %(company)s AND
                         sm.date <  %(datetime_from)s AND
                        (sm.location_id in %(locations)s OR sm.location_dest_id in %(locations)s)
                    left join stock_valuation_layer as svl on svl.stock_move_id = sm.id and
                            ((l10n_ro_valued_type !='internal_transfer' or
                                l10n_ro_valued_type is Null
                             ) or
                             (l10n_ro_valued_type ='internal_transfer' and quantity<0 and
                              sm.location_id in %(locations)s) or
                             (l10n_ro_valued_type ='internal_transfer' and quantity>0 and
                              sm.location_dest_id in %(locations)s))
                    where
                        ( %(all_products)s  or sm.product_id in %(product)s ) and svl.active = 't'
                    GROUP BY prod.id, svl.l10n_ro_account_id)
                a --where a.amount_initial!=0 and a.quantity_initial!=0
                """

                params.update({"reference": "INITIAL"})
                self.env.cr.execute(query_select_sold_init, params=params)
                # res = self.env.cr.dictfetchall()
                # self.env["l10n.ro.stock.storage.sheet.line"].create(res)
                _logger.info("start query_select_sold_final %s", location.name)
                query_select_sold_final = """
                insert into l10n_ro_stock_storage_sheet_line
                  (report_id, product_id, amount_final, quantity_final, unit_price_out,
                   account_id, date_time, date, reference, document, location_id)
                select * from(
                    SELECT %(report)s as report_id, sm.product_id as product_id,
                        COALESCE(sum(svl.value),0)  as amount_final,
                        COALESCE(sum(svl.quantity),0)  as quantity_final,
                        CASE
                            WHEN ROUND(COALESCE(sum(svl.quantity), 0), 5) != 0
                                THEN ROUND(COALESCE(sum(svl.value),0) / sum(svl.quantity), 2)
                            ELSE 0
                        END as unit_price_out,
                        COALESCE(svl.l10n_ro_account_id, Null) as account_id,
                        %(datetime_to)s::timestamp without time zone as date_time,
                        %(date_to)s::date as date,
                        %(reference)s as reference,
                        %(reference)s as document,
                        %(location)s as location_id
                    from stock_move as sm
                    inner join  stock_valuation_layer as svl on svl.stock_move_id = sm.id and
                            ((l10n_ro_valued_type !='internal_transfer' or
                              l10n_ro_valued_type is Null
                             ) or
                             (l10n_ro_valued_type ='internal_transfer' and quantity<0 and
                              sm.location_id in %(locations)s) or
                             (l10n_ro_valued_type ='internal_transfer' and quantity>0 and
                              sm.location_dest_id in %(locations)s))
                    where sm.state = 'done' AND
                        sm.company_id = %(company)s AND
                        ( %(all_products)s  or sm.product_id in %(product)s ) AND
                        sm.date <=  %(datetime_to)s AND
                        (sm.location_id in %(locations)s OR sm.location_dest_id in %(locations)s) AND
                        svl.active = 't'
                    GROUP BY sm.product_id, svl.l10n_ro_account_id)
                a --where a.amount_final!=0 and a.quantity_final!=0
                """

                params.update({"reference": "FINAL"})
                self.env.cr.execute(query_select_sold_final, params=params)
                # res = self.env.cr.dictfetchall()
                # self.env["l10n.ro.stock.storage.sheet.line"].create(res)
                _logger.info("start query_in %s", location.name)
                query_in = """
                insert into l10n_ro_stock_storage_sheet_line
                  (report_id, product_id, amount_in, quantity_in, unit_price_in,
                   account_id, invoice_id, date_time, date, reference,  location_id,
                   partner_id, picking_type_id, document, valued_type, invoice_date )
                select * from(


                SELECT  %(report)s as report_id, sm.product_id as product_id,
                        COALESCE(sum(svl_in.value),0)   as amount_in,
                        COALESCE(ROUND(sum(svl_in.quantity), 5), 0)   as quantity_in,
                        CASE
                            WHEN ROUND(COALESCE(sum(svl_in.quantity), 0), 5) != 0
                                THEN COALESCE(sum(svl_in.value),0) / sum(svl_in.quantity)
                            ELSE 0
                        END as unit_price_in,
                         svl_in.l10n_ro_account_id as account_id,
                         svl_in.l10n_ro_invoice_id as invoice_id,
                        sm.date as date_time,
                        date_trunc('day', sm.date at time zone 'utc' at time zone %(tz)s) as date,
                        sm.reference as reference,
                        %(location)s as location_id,
                        sp.partner_id,
                        sp.picking_type_id,
                        COALESCE(am.name, sm.reference) as document,
                        COALESCE(svl_in.l10n_ro_valued_type, 'indefinite') as valued_type,
                        am.invoice_date

                    from stock_move as sm
                        inner join stock_valuation_layer as svl_in
                            on svl_in.stock_move_id = sm.id and
                            (
                             (sm.location_dest_id in %(locations)s and svl_in.quantity>=0 and
                              l10n_ro_valued_type not like '%%_return')
                            or
                             (sm.location_id in %(locations)s and (svl_in.quantity<=0 and
                             l10n_ro_valued_type='reception_return'))
                            )
                        left join stock_picking as sp on sm.picking_id = sp.id
                        left join account_move am on svl_in.l10n_ro_invoice_id = am.id
                    where
                        sm.state = 'done' AND
                        sm.company_id = %(company)s AND
                        ( %(all_products)s  or sm.product_id in %(product)s ) AND
                        sm.date >= %(datetime_from)s  AND  sm.date <= %(datetime_to)s  AND
                        (sm.location_dest_id in %(locations)s or sm.location_id in %(locations)s) AND
                        svl_in.active = 't'
                    GROUP BY sm.product_id, sm.date,
                     sm.reference, sp.partner_id, sp.picking_type_id, l10n_ro_account_id,
                     svl_in.l10n_ro_invoice_id, am.name, am.invoice_date, svl_in.l10n_ro_valued_type)
                a --where a.amount_in!=0 and a.quantity_in!=0
                    """
                self.env.cr.execute(query_in, params=params)
                # res = self.env.cr.dictfetchall()
                # self.env["l10n.ro.stock.storage.sheet.line"].create(res)
                _logger.info("start query_out %s", location.name)
                query_out = """
                            insert into l10n_ro_stock_storage_sheet_line
                  (report_id, product_id, amount_out, quantity_out, unit_price_out,
                   account_id, invoice_id, date_time, date, reference,  location_id,
                   partner_id, picking_type_id, document, valued_type, invoice_date )

                select * from(

                SELECT  %(report)s as report_id, sm.product_id as product_id,
                        -1*COALESCE(sum(svl_out.value),0)   as amount_out,
                        -1*COALESCE(ROUND(sum(svl_out.quantity), 5),0) as quantity_out,
                        CASE
                            WHEN ROUND(COALESCE(sum(svl_out.quantity), 0), 5) != 0
                                THEN COALESCE(sum(svl_out.value),0) / sum(svl_out.quantity)
                            ELSE 0
                        END as unit_price_out,
                        svl_out.l10n_ro_account_id as account_id,
                        svl_out.l10n_ro_invoice_id as invoice_id,
                        sm.date as date_time,
                        date_trunc('day', sm.date at time zone 'utc' at time zone %(tz)s) as date,
                        sm.reference as reference,
                        %(location)s as location_id,
                        sp.partner_id,
                        sp.picking_type_id,
                        COALESCE(am.name, sm.reference) as document,
                        COALESCE(svl_out.l10n_ro_valued_type, 'indefinite') as valued_type,
                        am.invoice_date

                    from stock_move as sm

                        inner join stock_valuation_layer as svl_out
                            on svl_out.stock_move_id = sm.id and
                             (
                              (sm.location_id in %(locations)s and svl_out.quantity<=0 and
                                l10n_ro_valued_type != 'reception_return')
                             or
                              (sm.location_dest_id in  %(locations)s and (svl_out.quantity>=0 and
                               l10n_ro_valued_type like '%%_return'))
                             )
                        left join stock_picking as sp on sm.picking_id = sp.id
                        left join account_move am on svl_out.l10n_ro_invoice_id = am.id
                    where
                        sm.state = 'done' AND
                        sm.company_id = %(company)s AND
                        ( %(all_products)s  or sm.product_id in %(product)s ) AND
                        sm.date >= %(datetime_from)s  AND  sm.date <= %(datetime_to)s  AND
                        (sm.location_id in %(locations)s or sm.location_dest_id in %(locations)s) AND
                        svl_out.active = 't'
                    GROUP BY sm.product_id, sm.date,
                             sm.reference, sp.partner_id, sp.picking_type_id, account_id,
                             svl_out.l10n_ro_invoice_id, am.name, am.invoice_date, svl_out.l10n_ro_valued_type)
                a --where a.amount_out!=0 and a.quantity_out!=0
                    """
                self.env.cr.execute(query_out, params=params)
                # res = self.env.cr.dictfetchall()
                # self.line_product_ids.create(res)
            _logger.info("end select ")


class StorageSheetLine(models.TransientModel):
    _inherit = "l10n.ro.stock.storage.sheet.line"

    picking_type_id = fields.Many2one("stock.picking.type", index=True)
    invoice_date = fields.Date(index=True)
