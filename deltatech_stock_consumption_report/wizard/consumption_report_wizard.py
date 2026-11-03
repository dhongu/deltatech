import base64
import io
from collections import defaultdict
from datetime import datetime, time, timedelta

import pytz
import xlsxwriter
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import format_date


class StockConsumptionReportWizard(models.TransientModel):
    _name = "stock.consumption.report.wizard"
    _description = "Consumption report"

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    date_from = fields.Date(
        required=True,
        default=lambda self: fields.Date.context_today(self).replace(day=1),
    )
    date_to = fields.Date(
        required=True,
        default=lambda self: fields.Date.context_today(self).replace(day=1) + relativedelta(months=1, days=-1),
    )
    picking_type_ids = fields.Many2many(
        "stock.picking.type",
        string="Operation types",
        domain=lambda self: [("default_location_dest_id.usage", "in", self._consumption_usages())],
        default=lambda self: self._default_picking_type_ids(),
        help="Leave empty to include every consumption movement of the period.",
    )
    file_data = fields.Binary(readonly=True, attachment=False)
    line_ids = fields.One2many("stock.consumption.report.line", "wizard_id")
    file_name = fields.Char(readonly=True)

    @api.model
    def _consumption_usages(self):
        return self.env["stock.location"]._get_consumption_usages()

    @api.model
    def _default_picking_type_ids(self):
        return self.env["stock.picking.type"].search(
            [
                ("company_id", "=", self.env.company.id),
                ("default_location_dest_id.usage", "in", self._consumption_usages()),
            ]
        )

    # ------------------------------------------------------------------
    # Selectie
    # ------------------------------------------------------------------
    def _to_utc(self, day, end=False):
        tz = pytz.timezone(self.env.user.tz or "UTC")
        local = datetime.combine(day + timedelta(days=1) if end else day, time.min)
        return tz.localize(local).astimezone(pytz.UTC).replace(tzinfo=None)

    def _get_moves_domain(self):
        self.ensure_one()
        domain = [
            ("state", "=", "done"),
            ("company_id", "=", self.company_id.id),
            ("location_dest_id.usage", "in", self._consumption_usages()),
            ("date", ">=", self._to_utc(self.date_from)),
            ("date", "<", self._to_utc(self.date_to, end=True)),
        ]
        if self.picking_type_ids:
            domain.append(("picking_type_id", "in", self.picking_type_ids.ids))
        return domain

    def action_view(self):
        """Pivotul se face pe liniile raportului, ca valorile sa fie aceleasi ca in XLSX."""
        self.ensure_one()
        self.line_ids.unlink()
        _summary, detail = self._get_report_data()
        self.env["stock.consumption.report.line"].create(
            [
                {
                    "wizard_id": self.id,
                    "store": line["store"],
                    "purpose": line["purpose"],
                    "product_id": line["product_id"],
                    "quantity": line["quantity"],
                    "value": line["value"],
                }
                for line in detail
            ]
        )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Consumption"),
            "res_model": "stock.consumption.report.line",
            "view_mode": "pivot,list",
            "views": [
                (
                    self.env.ref("deltatech_stock_consumption_report.view_stock_consumption_report_line_pivot").id,
                    "pivot",
                ),
                (False, "list"),
            ],
            "domain": [("wizard_id", "=", self.id)],
            "context": {},
        }

    # ------------------------------------------------------------------
    # Date
    # ------------------------------------------------------------------
    def _get_sold_quantities(self, products):
        """Cantitatea livrata catre clienti in ultimele 6 luni, pe produs, in UM produsului."""
        since = self._to_utc(self.date_to, end=True) - relativedelta(months=6)
        groups = self.env["stock.move"]._read_group(
            [
                ("state", "=", "done"),
                ("company_id", "=", self.company_id.id),
                ("product_id", "in", products.ids),
                ("location_dest_id.usage", "=", "customer"),
                ("date", ">=", since),
            ],
            ["product_id", "product_uom"],
            ["quantity:sum"],
        )
        sold = defaultdict(float)
        for product, uom, qty in groups:
            sold[product.id] += uom._compute_quantity(qty, product.uom_id, round=False)
        return sold

    def _get_move_values(self, moves):
        """Valoarea consumului pe miscare, din nota contabila a bonului: creditul liniilor
        produsului, adica iesirea din contul de stoc (contul poate depinde de locatie sau de
        depozit, de aceea nu se cauta dupa cont). Cand aceeasi nota are mai multe miscari ale
        aceluiasi produs, suma se imparte proportional cu cantitatea. Fara nota se foloseste
        valoarea de stoc a miscarii."""
        values = {}
        for entry in moves.account_move_id:
            entry_moves = entry.stock_move_ids
            for product in entry_moves.product_id:
                lines = entry.line_ids.filtered(lambda aml, p=product: aml.product_id == p and aml.credit)
                if not lines:
                    continue
                amount = sum(lines.mapped("credit"))
                product_moves = entry_moves.filtered(lambda m, p=product: m.product_id == p)
                total_qty = sum(product_moves.mapped("quantity"))
                for move in product_moves:
                    share = move.quantity / total_qty if total_qty else 1 / len(product_moves)
                    values[move.id] = amount * share
        return {move.id: values.get(move.id, move.value) for move in moves}

    def _get_report_data(self):
        """Intoarce (centralizat, detaliat). Magazinul e depozitul tipului de operatiune,
        destinatia e cea de pe bonul de consum."""
        self.ensure_one()
        moves = self.env["stock.move"].search(self._get_moves_domain())
        products = moves.product_id
        sold = self._get_sold_quantities(products)
        undefined = self.env._("Undefined")
        values = self._get_move_values(moves)

        detail = defaultdict(lambda: {"quantity": 0.0, "value": 0.0})
        for move in moves:
            store = move.picking_type_id.warehouse_id.name or move.picking_type_id.name or "-"
            purpose = move.picking_id.consumption_purpose_id.name or undefined
            key = (store, purpose, move.product_id.id)
            detail[key]["quantity"] += move.product_uom._compute_quantity(
                move.quantity, move.product_id.uom_id, round=False
            )
            detail[key]["value"] += values[move.id]

        product_map = {product.id: product for product in products}
        detail_rows = []
        summary = defaultdict(lambda: {"products": 0, "quantity": 0.0, "value": 0.0, "sold_products": 0})
        for (store, purpose, product_id), vals in sorted(detail.items()):
            product = product_map[product_id]
            qty = vals["quantity"]
            is_sold = bool(sold.get(product_id))
            detail_rows.append(
                {
                    "store": store,
                    "purpose": purpose,
                    "product_id": product_id,
                    "code": product.default_code or "",
                    "product": product.name,
                    "category": product.categ_id.complete_name or "",
                    "uom": product.uom_id.name,
                    "quantity": qty,
                    "value": vals["value"],
                    "avg_cost": vals["value"] / qty if qty else 0.0,
                    "sale_ok": product.sale_ok,
                    "sold_6m": sold.get(product_id, 0.0),
                }
            )
            line = summary[(store, purpose)]
            line["products"] += 1
            line["quantity"] += qty
            line["value"] += vals["value"]
            line["sold_products"] += 1 if is_sold else 0
        summary_rows = [
            {"store": store, "purpose": purpose, **vals} for (store, purpose), vals in sorted(summary.items())
        ]
        return summary_rows, detail_rows

    # ------------------------------------------------------------------
    # Export XLSX
    # ------------------------------------------------------------------
    def action_export_xlsx(self):
        self.ensure_one()
        env = self.env
        summary_rows, detail_rows = self._get_report_data()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        header = workbook.add_format({"bold": True, "bg_color": "#D9E1F2", "border": 1, "text_wrap": True})
        number = workbook.add_format({"num_format": "#,##0.00"})
        total = workbook.add_format({"bold": True, "num_format": "#,##0.00", "top": 1})
        total_label = workbook.add_format({"bold": True, "top": 1})
        total_count = workbook.add_format({"bold": True, "num_format": "0", "top": 1})
        title = workbook.add_format({"bold": True, "font_size": 12})
        period = env._(
            "Period: %(date_from)s - %(date_to)s",
            date_from=format_date(env, self.date_from),
            date_to=format_date(env, self.date_to),
        )
        yes, no = env._("Yes"), env._("No")

        sheet = workbook.add_worksheet(env._("Summary"))
        sheet.write(0, 0, env._("Consumption summary by store and purpose"), title)
        sheet.write(1, 0, period)
        columns = [
            env._("Store"),
            env._("Purpose"),
            env._("Products"),
            env._("Quantity"),
            env._("Value"),
            env._("Products sold in the last 6 months"),
        ]
        for col, label in enumerate(columns):
            sheet.write(3, col, label, header)
        row = 4
        for line in summary_rows:
            sheet.write(row, 0, line["store"])
            sheet.write(row, 1, line["purpose"])
            sheet.write(row, 2, line["products"])
            sheet.write(row, 3, line["quantity"], number)
            sheet.write(row, 4, line["value"], number)
            sheet.write(row, 5, line["sold_products"])
            row += 1
        if summary_rows:
            sheet.write(row, 0, env._("Total"), total_label)
            for col, key, cell_format in (
                (2, "products", total_count),
                (3, "quantity", total),
                (4, "value", total),
                (5, "sold_products", total_count),
            ):
                sheet.write(row, col, sum(line[key] for line in summary_rows), cell_format)
        sheet.set_column(0, 1, 30)
        sheet.set_column(2, 5, 18)

        sheet = workbook.add_worksheet(env._("Detail"))
        sheet.write(0, 0, env._("Consumption detail by product"), title)
        sheet.write(1, 0, period)
        columns = [
            env._("Store"),
            env._("Purpose"),
            env._("Code"),
            env._("Product"),
            env._("Category"),
            env._("UoM"),
            env._("Quantity"),
            env._("Value"),
            env._("Average cost"),
            env._("Can be sold"),
            env._("Delivered to customers (last 6 months)"),
        ]
        for col, label in enumerate(columns):
            sheet.write(3, col, label, header)
        row = 4
        for line in detail_rows:
            sheet.write(row, 0, line["store"])
            sheet.write(row, 1, line["purpose"])
            sheet.write(row, 2, line["code"])
            sheet.write(row, 3, line["product"])
            sheet.write(row, 4, line["category"])
            sheet.write(row, 5, line["uom"])
            sheet.write(row, 6, line["quantity"], number)
            sheet.write(row, 7, line["value"], number)
            sheet.write(row, 8, line["avg_cost"], number)
            sheet.write(row, 9, yes if line["sale_ok"] else no)
            sheet.write(row, 10, line["sold_6m"], number)
            row += 1
        if detail_rows:
            sheet.write(row, 0, env._("Total"), total_label)
            sheet.write(row, 7, sum(line["value"] for line in detail_rows), total)
        sheet.set_column(0, 1, 24)
        sheet.set_column(2, 2, 14)
        sheet.set_column(3, 4, 40)
        sheet.set_column(5, 10, 16)
        sheet.freeze_panes(4, 4)
        workbook.close()

        self.write(
            {
                "file_data": base64.b64encode(output.getvalue()),
                "file_name": f"consumuri_{self.date_from:%Y-%m-%d}_{self.date_to:%Y-%m-%d}.xlsx",
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }


class StockConsumptionReportLine(models.TransientModel):
    _name = "stock.consumption.report.line"
    _description = "Consumption report line"

    wizard_id = fields.Many2one("stock.consumption.report.wizard", required=True, ondelete="cascade")
    store = fields.Char()
    purpose = fields.Char()
    product_id = fields.Many2one("product.product", readonly=True)
    categ_id = fields.Many2one(related="product_id.categ_id")
    currency_id = fields.Many2one(related="wizard_id.company_id.currency_id")
    quantity = fields.Float(digits="Product Unit")
    value = fields.Monetary()
