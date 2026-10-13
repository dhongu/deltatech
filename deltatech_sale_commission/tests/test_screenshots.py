# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Comisioane de vânzare calculate din profit" — generate în
# timpul testelor, în limba RO, pe compania „Demo Distribuție SRL" în RON.
#
# Seed: agenta Ana Popescu, cu manager și director, are comision 10 % din profit (manager 2 %,
# director 1 %) pe jurnalul de facturi clienți. Trei facturi din luna trecută (filtrul implicit
# al rapoartelor), fiecare dintr-o comandă livrată, deci cu costul luat din livrare:
#   - FV1: 10 × Laptop 14" la 3.500 lei, cost 2.800 → profit 7.000; plătită la 3 zile după
#     scadență → primește comision;
#   - FV2: 5 × Monitor 27" la 1.400 lei, cost 1.000 → profit 2.000; plătită la 20 de zile după
#     scadență, peste limita de 10 zile → comision 0;
#   - FV3: 20 × Mouse la 90 lei, cost 50 → profit 800; neplătită → comision 0.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_sale_commission,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import logging
import unittest

from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

_logger = logging.getLogger(__name__)

# Selectează toate rândurile listei, deschide „Acțiuni" (⚙) și alege intrarea potrivită.
JS_SELECT_ALL_ACTION = """
async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    document.querySelector('thead .o_list_record_selector input').click();
    await sleep(1000);
    const toggle = [...document.querySelectorAll('.o_control_panel button')]
        .find((b) => /Acțiuni|Actions/.test(b.textContent));
    toggle.click();
    await sleep(1000);
    const items = [...document.querySelectorAll('.o-dropdown-item, .dropdown-item')];
    items.find((e) => %(match)s.test(e.textContent)).click();
    await sleep(2500);
}
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSaleCommissionScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_sale_commission"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Distribuție SRL")
        company = cls.company = cls.env.company
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        (admin | env.user).tz = "Europe/Bucharest"
        groups = [
            "sales_team.group_sale_manager",
            "stock.group_stock_manager",
            "deltatech_sale_commission.group_commission_manager",
            "deltatech_sale_margin.group_sale_margin",
        ]
        for xmlid in groups:
            group = env.ref(xmlid)
            admin.group_ids = [Command.link(group.id)]
            env.user.group_ids = [Command.link(group.id)]
        env.flush_all()

        # baza poate avea produse demo: le arhivăm, ca listele să arate doar produsele fluxului
        env["product.template"].sudo().search([]).active = False

        def user(name, login):
            return (
                env["res.users"]
                .with_context(no_reset_password=True)
                .create(
                    {
                        "name": name,
                        "login": login,
                        "company_id": company.id,
                        "company_ids": [Command.set(company.ids)],
                        "group_ids": [Command.set(env.ref("sales_team.group_sale_salesman").ids)],
                    }
                )
            )

        cls.agent = user("Ana Popescu", "ana.popescu")
        cls.manager = user("Mihai Ionescu", "mihai.ionescu")
        cls.director = user("Elena Marin", "elena.marin")

        cls.sale_journal = env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", company.id)], limit=1
        )
        cls.bank_journal = env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", company.id)], limit=1
        )
        env["commission.users"].create(
            {
                "user_id": cls.agent.id,
                "rate": 0.10,
                "manager_user_id": cls.manager.id,
                "manager_rate": 0.02,
                "director_user_id": cls.director.id,
                "director_rate": 0.01,
                "journal_id": cls.sale_journal.id,
                "company_id": company.id,
            }
        )
        # comisionul se acordă doar pe facturile încasate cel târziu la 10 zile după scadență
        env["ir.config_parameter"].sudo().set_param("deltatech_sale_commission.days_for_commission", "10")

        cls.categ = env["product.category"].create({"name": "IT & periferice"})
        cls.categ.with_company(company).property_cost_method = "fifo"
        cls.wh = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        cls.wh.write({"name": "Depozit central", "code": "WH"})
        suppliers = env.ref("stock.stock_location_suppliers")

        def product(name, cost, price, qty):
            prod = env["product.product"].create(
                {
                    "name": name,
                    "type": "consu",
                    "is_storable": True,
                    "categ_id": cls.categ.id,
                    "standard_price": cost,
                    "list_price": price,
                    "company_id": company.id,
                }
            )
            # recepție cu preț, ca livrarea să ia costul real (FIFO) al mărfii
            move = env["stock.move"].create(
                {
                    "product_id": prod.id,
                    "product_uom": prod.uom_id.id,
                    "product_uom_qty": qty,
                    "price_unit": cost,
                    "location_id": suppliers.id,
                    "location_dest_id": cls.wh.lot_stock_id.id,
                    "company_id": company.id,
                }
            )
            move._action_confirm()
            move.quantity = qty
            move.picked = True
            move._action_done()
            return prod

        cls.laptop = product('Laptop 14"', 2800.0, 3500.0, 50)
        cls.monitor = product('Monitor 27"', 1000.0, 1400.0, 50)
        cls.mouse = product("Mouse wireless", 50.0, 90.0, 100)

        ro = env.ref("base.ro")
        state_b = env["res.country.state"].search([("country_id", "=", ro.id), ("code", "=", "B")], limit=1)
        cls.customer = env["res.partner"].create(
            {
                "name": "Birotica Plus SRL",
                "is_company": True,
                "vat": "RO18547290",
                "country_id": ro.id,
                "state_id": state_b.id,
                "city": "București",
                "street": "Bd. Unirii nr. 20",
            }
        )

        # facturile sunt datate în luna trecută: rapoartele se deschid cu filtrul pe luna trecută
        today = fields.Date.context_today(env["res.partner"])
        cls.invoice_date = (today - relativedelta(months=1)).replace(day=1)
        immediate = env.ref("account.account_payment_term_immediate")

        def sell(prod, qty, price, paid_after_days=None):
            order = env["sale.order"].create(
                {
                    "partner_id": cls.customer.id,
                    "user_id": cls.agent.id,
                    "payment_term_id": immediate.id,
                    "order_line": [
                        Command.create({"product_id": prod.id, "product_uom_qty": qty, "price_unit": price})
                    ],
                }
            )
            order.action_confirm()
            picking = order.picking_ids
            for move in picking.move_ids:
                move.quantity = move.product_uom_qty
            picking.move_ids.picked = True
            picking._action_done()
            # livrarea înaintea facturii, în aceeași lună (altfel factura arată livrarea „azi")
            delivered = fields.Datetime.to_datetime(cls.invoice_date) - relativedelta(hours=12)
            picking.write({"date_done": delivered})
            picking.move_ids.write({"date": delivered})
            invoice = order._create_invoices()
            invoice.write({"invoice_date": cls.invoice_date, "invoice_user_id": cls.agent.id})
            invoice.action_post()
            if paid_after_days is not None:
                env["account.payment.register"].with_context(
                    active_model="account.move", active_ids=invoice.ids
                ).create(
                    {
                        "payment_date": invoice.invoice_date_due + relativedelta(days=paid_after_days),
                        "journal_id": cls.bank_journal.id,
                    }
                )._create_payments()
            return invoice

        cls.inv_on_time = sell(cls.laptop, 10, 3500.0, paid_after_days=3)
        cls.inv_late = sell(cls.monitor, 5, 1400.0, paid_after_days=20)
        cls.inv_unpaid = sell(cls.mouse, 20, 90.0)
        env.flush_all()
        env["sale.margin.report"].invalidate_model()
        for inv in cls.inv_on_time | cls.inv_late | cls.inv_unpaid:
            line = env["sale.margin.report"].search([("invoice_id", "=", inv.id)])
            _logger.info(
                "COMISION %s: plată %s, vânzare %s, cost %s, profit %s, calculat %s / manager %s / director %s",
                inv.name,
                inv.payment_state,
                line.mapped("sale_val"),
                line.mapped("stock_val"),
                line.mapped("profit_val"),
                line.mapped("commission_computed"),
                line.mapped("commission_manager_computed"),
                line.mapped("commission_director_computed"),
            )

        cls.act_settings = env.ref("sale.action_sale_config_settings")
        cls.act_users = env.ref("deltatech_sale_commission.action_commission_users")
        cls.act_invoices = env.ref("account.action_move_out_invoice_type")
        cls.act_margin = env.ref("deltatech_sale_commission.action_sale_margin_report")
        cls.act_commission = env.ref("deltatech_sale_commission.action_sale_margin_commission_report")

    def _capture(self, shots):
        self.env.flush_all()
        self.capture_screenshots(shots)
        self.env.invalidate_all()

    def _commission_list(self, name, **extra):
        shot = {
            "url": f"action={self.act_commission.id}&view_type=list",
            "name": name,
            "wait": ".o_list_view",
            "settle": 2500,
        }
        shot.update(extra)
        return shot

    def test_capture_fise(self):
        self._capture(
            [
                {
                    "url": f"action={self.act_settings.id}",
                    "name": "01_setari_agent_comision.png",
                    "wait": ".o_form_view",
                    "timeout": 40000,
                    "settle": 3000,
                    "eval": "document.querySelector(\"div[name='sale_user_detail']\")"
                    ".scrollIntoView({block: 'center'})",
                    "highlight": ["div[name='sale_user_detail']"],
                },
                {
                    "url": f"action={self.act_users.id}&view_type=list",
                    "name": "02_comisioane_agenti.png",
                    "wait": ".o_list_view",
                    "settle": 2000,
                },
                {
                    "url": f"action={self.act_invoices.id}&id={self.inv_on_time.id}&model=account.move&view_type=form",
                    "name": "03_factura_pret_cost.png",
                    "wait": ".o_form_view",
                    "settle": 2500,
                    "highlight": ["td[name='purchase_price']"],
                },
                {
                    "url": f"action={self.act_margin.id}&view_type=pivot",
                    "name": "04_raport_profit.png",
                    "wait": ".o_pivot",
                    "settle": 3000,
                },
                self._commission_list("05_comisioane_de_calculat.png"),
                self._commission_list(
                    "06_calcul_comisioane.png",
                    eval=JS_SELECT_ALL_ACTION % {"match": "/Calcul comisioane|Compute Commission/"},
                    eval_wait=1500,
                ),
            ]
        )

        # aplicarea calculului pe liniile facturilor plătite (filtrul implicit al listei)
        lines = self.env["sale.margin.report"].search([("payment_state", "=", "paid")])
        self.env["commission.compute"].with_context(active_ids=lines.ids).create({}).do_compute()
        self._capture([self._commission_list("07_comisioane_calculate.png")])

        # comisionul plătit agentei: linia facturii la timp se marchează plătită
        self.env["sale.margin.report"].search([("invoice_id", "=", self.inv_on_time.id)]).action_set_commission_paid()
        self._capture(
            [
                self._commission_list("08_comisioane_platite.png"),
                self._commission_list(
                    "09_actualizare_pret_achizitie.png",
                    eval=JS_SELECT_ALL_ACTION % {"match": "/Actualizare preț achiziție|Update Purchase Price/"},
                    eval_wait=1500,
                ),
            ]
        )
