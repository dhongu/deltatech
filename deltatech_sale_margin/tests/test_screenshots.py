# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Control al marjei pe comanda de vânzare" — generate în
# timpul testelor, în limba RO, pe compania „Demo Marjă SRL" în RON.
#
# Seedează politica „Doar avertisment" și o comandă vândută sub cost pe ambalaj
# (cost 3 lei/kg → 36 lei/Cutie 12 kg, vândut la 30 lei/cutie), ca să arate atât
# semnalul, cât și faptul că vânzarea NU e blocată.
#
# Pentru costul pe factură și raportul de profit: două facturi din luna trecută (filtrul
# implicit al raportului), fiecare dintr-o comandă livrată, deci cu costul luat din livrare:
#   - 10 × Laptop 14" la 3.500 lei, cost 2.800 → profit 7.000;
#   - 5 × Monitor 27" la 1.400 lei, cost 1.000 → profit 2.000.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_sale_margin,l10n_ro,l10n_ro_doc_screenshots \
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

# Scoate gruparea „Produs" din bara de căutare (× pe fațetă), ca rândurile să apară una câte una.
JS_REMOVE_PRODUCT_GROUPING = """
    const facet = [...document.querySelectorAll('.o_searchview_facet')]
        .find((f) => /Produs|Product/.test(f.textContent));
    facet.querySelector('.o_facet_remove').click();
    await sleep(2000);
"""

# Selectează toate rândurile listei (după pașii de pregătire din „before"), deschide „Acțiuni" (⚙) și alege intrarea potrivită.
JS_SELECT_ALL_ACTION = """
async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    %(before)s
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
class TestSaleMarginScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_sale_margin"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Marjă SRL")
        company = cls.env.company
        env = cls.env
        env.ref("base.user_admin").write({"company_ids": [Command.link(company.id)], "company_id": company.id})

        # drepturi de vânzări pe utilizatorul testului (seedează) și pe admin (e cel
        # autentificat în browserul de capturi)
        sale_manager = env.ref("sales_team.group_sale_manager", raise_if_not_found=False)
        if sale_manager:
            env.user.group_ids = [Command.link(sale_manager.id)]
            env.ref("base.user_admin").group_ids = [Command.link(sale_manager.id)]
        # „Unități de măsură": fără grupul ăsta coloana unității nu apare deloc în
        # captură, iar vânzarea pe ambalaj — miezul exemplului — nu s-ar vedea
        env["res.config.settings"].create({"group_uom": True}).execute()
        env.user.group_ids |= env.ref("uom.group_uom")
        env.ref("base.user_admin").group_ids |= env.ref("uom.group_uom")
        env.flush_all()

        # politica pusă pe „Doar avertisment": implicitul e „Blochează vânzarea", pe
        # care nu îl putem ilustra cu o captură (blocajul e un dialog de eroare)
        company.sale_margin_check_mode = "warn"
        env["ir.config_parameter"].sudo().set_param("sale.margin_limit", "0")
        env["ir.config_parameter"].sudo().set_param("sale.margin_limit_check_validate", "0")

        cls.partner = env["res.partner"].create({"name": "Lanț Retail SRL", "country_id": env.ref("base.ro").id})
        cls.partner.property_product_pricelist.name = "Listă de prețuri clienți RON"

        cls.uom_kg = env.ref("uom.product_uom_kgm")
        cls.uom_box = env["uom.uom"].create(
            {"name": "Cutie 12 kg", "relative_factor": 12.0, "relative_uom_id": cls.uom_kg.id}
        )
        # costul stă pe kg, vânzarea se face pe cutie: 3 lei/kg = 36 lei/cutie
        cls.product = env["product.product"].create(
            {
                "name": "Mere Idared calibru 70+",
                "type": "consu",
                "is_storable": True,
                "uom_id": cls.uom_kg.id,
                "standard_price": 3.0,
                "list_price": 3.5,
            }
        )
        # 30 lei/cutie e SUB costul convertit de 36 lei/cutie. O comparație
        # neconvertită (30 față de 3 lei/kg) ar arăta o marjă de 90% și ar rata
        # exact vânzările în ambalaje.
        cls.order = env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 10,
                            "product_uom_id": cls.uom_box.id,
                            "price_unit": 30.0,
                        }
                    )
                ],
            }
        )
        # a doua comandă, confirmată: dovedește în seed-ul capturilor că
        # `action_confirm` trece pe modul „warn" (pe „block" ar fi aruncat).
        # Nota din chatter NU are captură proprie: chatterul cade în mod
        # constant în afara cadrului capturat, iar nota e un efect al
        # confirmării, nu un ecran separat — e descrisă în pasul 2 al fișei.
        cls.order_confirmed = cls.order.copy()
        cls.order_confirmed.action_confirm()
        cls.settings_action = env.ref("sale.action_sale_config_settings")
        cls._seed_invoices()

    @classmethod
    def _seed_invoices(cls):
        """Două facturi din comenzi livrate, pentru costul pe factură și raportul de profit."""
        env = cls.env
        company = env.company
        admin = env.ref("base.user_admin")
        for xmlid in ("stock.group_stock_manager", "deltatech_sale_margin.group_sale_margin"):
            group = env.ref(xmlid)
            admin.group_ids = [Command.link(group.id)]
            env.user.group_ids = [Command.link(group.id)]
        (admin | env.user).tz = "Europe/Bucharest"
        env.flush_all()

        categ = env["product.category"].create({"name": "IT & periferice"})
        categ.with_company(company).property_cost_method = "fifo"
        wh = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        suppliers = env.ref("stock.stock_location_suppliers")

        def product(name, cost, price, qty):
            prod = env["product.product"].create(
                {
                    "name": name,
                    "type": "consu",
                    "is_storable": True,
                    "categ_id": categ.id,
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
                    "location_dest_id": wh.lot_stock_id.id,
                    "company_id": company.id,
                }
            )
            move._action_confirm()
            move.quantity = qty
            move.picked = True
            move._action_done()
            return prod

        ro = env.ref("base.ro")
        state_b = env["res.country.state"].search([("country_id", "=", ro.id), ("code", "=", "B")], limit=1)
        customer = env["res.partner"].create(
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
        # facturile sunt datate în luna trecută: raportul se deschide cu filtrul pe luna trecută
        today = fields.Date.context_today(env["res.partner"])
        invoice_date = (today - relativedelta(months=1)).replace(day=1)

        def sell(prod, qty, price):
            order = env["sale.order"].create(
                {
                    "partner_id": customer.id,
                    "payment_term_id": env.ref("account.account_payment_term_immediate").id,
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
            delivered = fields.Datetime.to_datetime(invoice_date) - relativedelta(hours=12)
            picking.write({"date_done": delivered})
            picking.move_ids.write({"date": delivered})
            invoice = order._create_invoices()
            invoice.write({"invoice_date": invoice_date})
            invoice.action_post()
            return invoice

        cls.invoice = sell(product('Laptop 14"', 2800.0, 3500.0, 50), 10, 3500.0)
        sell(product('Monitor 27"', 1000.0, 1400.0, 50), 5, 1400.0)
        env.flush_all()
        cls.act_invoices = env.ref("account.action_move_out_invoice_type")
        cls.act_margin = env.ref("deltatech_sale_margin.action_sale_margin_report")

    def test_capture_fise(self):
        self.capture_screenshots(
            [
                # 1. Politica și pragul, în Setări → Vânzări → Prețuri
                {
                    "url": f"action={self.settings_action.id}",
                    "name": "01_setari_politica.png",
                    "wait": ".o_form_view",
                    "settle": 3000,
                    "full": True,
                    "highlight": ["div[name='sale_margin_check_mode']"],
                },
                # 2. Semnalul pe comandă: bannerul + rândul marcat, cu Confirmă activ
                {
                    "url": f"id={self.order.id}&model=sale.order&view_type=form",
                    "name": "02_comanda_sub_cost.png",
                    "wait": ".o_form_view",
                    "settle": 2500,
                    "full": True,
                    "highlight": [".alert-warning", "div[name='order_line']"],
                },
                # 3. Costul pe factura client, luat din livrare
                {
                    "url": f"action={self.act_invoices.id}&id={self.invoice.id}&model=account.move&view_type=form",
                    "name": "03_factura_pret_cost.png",
                    "wait": ".o_form_view",
                    "settle": 2500,
                    "highlight": ["td[name='purchase_price']"],
                },
                # 4. Raportul de analiză a profitului (pivot)
                {
                    "url": f"action={self.act_margin.id}&view_type=pivot",
                    "name": "04_raport_profit.png",
                    "wait": ".o_pivot",
                    "settle": 3000,
                },
                # 5. Recalcularea costului, din lista raportului
                {
                    "url": f"action={self.act_margin.id}&view_type=list",
                    "name": "05_actualizare_pret_achizitie.png",
                    "wait": ".o_list_view",
                    "settle": 2500,
                    # ca în fișă: întâi se scoate gruparea „Produs" din căutare, apoi se selectează liniile
                    "eval": JS_SELECT_ALL_ACTION
                    % {
                        "before": JS_REMOVE_PRODUCT_GROUPING,
                        "match": "/Actualizare preț achiziție|Update Purchase Price/",
                    },
                    "eval_wait": 1500,
                },
            ]
        )
