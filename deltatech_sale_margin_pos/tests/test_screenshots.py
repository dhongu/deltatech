# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Vânzările POS nefacturate în raportul de profit" — generate în
# timpul testelor, în limba RO, pe compania „Demo Magazin SRL" în RON.
#
# Seed, în luna trecută (filtrul implicit al raportului):
#   - o factură client: 2 × Espressor la 1.200 lei, cost 800 → profit 800;
#   - bonul 1, nefacturat: 3 × Cafea boabe 1 kg la 69 lei, cost 45 → profit 72;
#   - bonul 2, nefacturat: 1 × Espressor la 1.200 lei, cost 800 → profit 400;
#   - returul bonului 2: −1 × Espressor → −1.200 lei vânzare, −800 cost;
#   - bonul 4, facturat (azi): 2 × Cafea; apare în raport o singură dată, prin factura lui.
# Produsele au TVA 21 %: raportul arată vânzarea fără TVA (bonul 1: 207 lei, 250,47 cu TVA).
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_sale_margin_pos,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSaleMarginPosScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_sale_margin_pos"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Magazin SRL")
        company = cls.env.company
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        (admin | env.user).tz = "Europe/Bucharest"
        for xmlid in (
            "sales_team.group_sale_manager",
            "stock.group_stock_manager",
            "point_of_sale.group_pos_manager",
            "deltatech_sale_margin.group_sale_margin",
        ):
            group = env.ref(xmlid)
            admin.group_ids = [Command.link(group.id)]
            env.user.group_ids = [Command.link(group.id)]
        env.flush_all()

        # baza poate avea produse demo: le arhivăm, ca raportul să arate doar produsele fluxului
        env["product.template"].sudo().search([]).active = False

        cls.vat = env["account.tax"].search(
            [("type_tax_use", "=", "sale"), ("amount", "=", 21.0), ("company_id", "=", company.id)], limit=1
        )

        def product(name, cost, price):
            return env["product.product"].create(
                {
                    "name": name,
                    "type": "consu",
                    "standard_price": cost,
                    "list_price": price,
                    "taxes_id": [Command.set(cls.vat.ids)],
                    "available_in_pos": True,
                    "company_id": company.id,
                }
            )

        cls.coffee = product("Cafea boabe 1 kg", 45.0, 69.0)
        cls.espresso = product("Espressor automat", 800.0, 1200.0)
        cls.customer = env["res.partner"].create(
            {"name": "Cafeneaua Veche SRL", "is_company": True, "country_id": env.ref("base.ro").id}
        )

        today = fields.Date.context_today(env["res.partner"])
        cls.day = (today - relativedelta(months=1)).replace(day=10)
        day_time = fields.Datetime.to_datetime(cls.day) + relativedelta(hours=9)

        # o factură client obișnuită, ca raportul să arate ambele surse
        invoice = env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.customer.id,
                "invoice_date": cls.day,
                "invoice_line_ids": [
                    Command.create({"product_id": cls.espresso.id, "quantity": 2, "price_unit": 1200.0})
                ],
            }
        )
        invoice.action_post()

        cash_journal = env["account.journal"].search([("type", "=", "cash"), ("company_id", "=", company.id)], limit=1)
        cls.cash = env["pos.payment.method"].create(
            {"name": "Numerar", "journal_id": cash_journal.id, "company_id": company.id}
        )
        cls.pos_config = env["pos.config"].create(
            {"name": "Magazin Centru", "payment_method_ids": [Command.set(cls.cash.ids)], "company_id": company.id}
        )
        # jurnalul comenzilor casei se creează cu numele în engleză („Point of Sale")
        cls.pos_config.journal_id.name = "Casa Magazin Centru"
        # casiera care emite bonurile: apare pe bon și ca agent în raport
        cls.cashier = (
            env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Ioana Vasile",
                    "login": "ioana.vasile",
                    "company_id": company.id,
                    "company_ids": [Command.set(company.ids)],
                    "group_ids": [Command.set(env.ref("point_of_sale.group_pos_user").ids)],
                }
            )
        )
        cls.pos_config.open_ui()
        session = cls.pos_config.current_session_id
        session.set_opening_control(0, None)

        def pos_order(prod, qty, partner=None):
            amount = qty * prod.list_price
            amount_incl = round(amount * 1.21, 2)
            order = env["pos.order"].create(
                {
                    "session_id": session.id,
                    "partner_id": partner.id if partner else False,
                    "lines": [
                        Command.create(
                            {
                                "name": prod.name,
                                "product_id": prod.id,
                                "qty": qty,
                                "price_unit": prod.list_price,
                                "price_subtotal": amount,
                                "price_subtotal_incl": amount_incl,
                                "tax_ids": [Command.set(cls.vat.ids)],
                            }
                        )
                    ],
                    "amount_total": amount_incl,
                    "amount_tax": round(amount_incl - amount, 2),
                    "amount_paid": 0.0,
                    "amount_return": 0.0,
                }
            )
            env["pos.make.payment"].with_context(active_ids=order.ids, active_id=order.id).create(
                {"amount": amount_incl, "payment_method_id": cls.cash.id}
            ).check()
            order.write({"date_order": day_time, "user_id": cls.cashier.id})
            return order

        cls.order_coffee = pos_order(cls.coffee, 3)
        cls.order_espresso = pos_order(cls.espresso, 1)
        cls.order_return = pos_order(cls.espresso, -1)
        cls.order_invoiced = pos_order(cls.coffee, 2, partner=cls.customer)
        # facturat azi (Odoo pune data facturii la facturarea bonului), deci în afara lunii trecute:
        # acțiunile de mai jos nu filtrează pe dată, ca să se vadă că bonul apare doar prin factură
        cls.order_invoiced.action_pos_order_invoice()
        env.flush_all()

        # Pentru capturi, aceeași acțiune a raportului cu filtrul „Vânzări POS” pus, respectiv cu
        # pivotul grupat pe jurnal, fără filtrul de dată (date de test, anulate la final).
        report_action = env.ref("deltatech_sale_margin.action_sale_margin_report")
        # numele copiei, în română: copia scrie numele în limba mediului, iar interfața în RO îl
        # citește de acolo
        report_name = report_action.with_context(lang="ro_RO").name
        cls.act_pos_list = report_action.copy(
            {
                "name": report_name,
                "view_mode": "list",
                "view_id": env.ref("deltatech_sale_margin.view_sale_margin_report_list").id,
                "context": "{'search_default_pos_sales': 1}",
            }
        )
        cls.act_by_journal = report_action.copy(
            {
                "name": report_name,
                "context": "{'pivot_row_groupby': ['journal_id', 'product_id']}",
            }
        )
        cls.act_pos_orders = env.ref("point_of_sale.action_pos_pos_form")
        # capturile raportului, în aplicația Vânzări, ca în calea din fișă
        cls.sale_menu = env.ref("sale.sale_menu_root")

    def test_capture_fise(self):
        self.env.flush_all()
        self.capture_screenshots(
            [
                {
                    "url": f"action={self.act_pos_orders.id}&id={self.order_coffee.id}&model=pos.order&view_type=form",
                    "name": "01_bon_pos_nefacturat.png",
                    "wait": ".o_form_view",
                    "settle": 2500,
                },
                {
                    "url": f"action={self.act_by_journal.id}&menu_id={self.sale_menu.id}&view_type=pivot",
                    "name": "02_raport_profit_pe_jurnal.png",
                    "wait": ".o_pivot",
                    "settle": 3000,
                },
                {
                    "url": f"action={self.act_pos_list.id}&menu_id={self.sale_menu.id}&view_type=list",
                    "name": "03_vanzari_pos_in_raport.png",
                    "wait": ".o_list_view",
                    "settle": 2500,
                    "highlight": ["th[data-name='pos_order_id']"],
                },
            ]
        )
