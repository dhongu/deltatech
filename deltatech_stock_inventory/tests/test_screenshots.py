# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Inventariere pe document (metoda clasică, cu valori)" —
# generate în timpul testelor, în limba RO, pe compania „Demo Inventar SRL" în RON.
#
# Seed: două depozite (WH, WH2), categoria „Mărfuri" FIFO cu evaluare automatizată pe 371,
# locația de ajustare cu contul de pierderi 607 și trei produse cu stoc în WH. Inventarul
# principal are un minus (Șurub M8, 5 buc × 2 lei), un plus (Vopsea albă 5L, 2 buc × 80 lei)
# și o linie nenumărată (Diblu 8 mm). Capturile se fac pe faze, pentru că același document
# trece prin stări diferite: ciornă → în desfășurare → numărat → validat.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_stock_inventory,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

REPORT_POSITION = "deltatech_stock_inventory.report_inventory_position"
REPORT_DIFF = "deltatech_stock_inventory.report_inventory_diff"

# Deschide meniul „Acțiuni" (⚙) al vizualizării curente și alege intrarea care conține textul dat.
# Opțional selectează întâi rândurile de listă care conțin `rows` (pentru acțiunile pe selecție).
JS_ACTION_MENU = """
async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const rowsText = %(rows)s;
    if (rowsText) {
        const rows = [...document.querySelectorAll('.o_data_row')]
            .filter((r) => r.textContent.includes(rowsText));
        for (const r of rows) {
            r.querySelector('.o_list_record_selector input').click();
            await sleep(400);
        }
        await sleep(800);
    }
    const toggle = [...document.querySelectorAll('.o_control_panel button')]
        .find((b) => /Acțiuni|Actions/.test(b.textContent)) || document.querySelector('.o_cp_action_menus button');
    toggle.click();
    await sleep(1000);
    const items = [...document.querySelectorAll('.o-dropdown-item, .dropdown-item')];
    const item = items.find((e) => %(match)s.test(e.textContent));
    item.click();
    await sleep(2500);
}
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestStockInventoryScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_stock_inventory"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Inventar SRL")
        company = cls.company = cls.env.company
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        # utilizatorul testului apare ca autor al documentelor și în referința mișcărilor
        env.user.name = "Ion Gestionar"
        # același fus orar în interfață și în PDF (altfel orele diferă între capturi)
        (admin | env.user).tz = "Europe/Bucharest"

        # admin e cel autentificat în browser; utilizatorul testului seedează
        for xmlid in (
            "stock.group_stock_manager",
            "stock.group_stock_multi_locations",
            "stock.group_stock_multi_warehouses",
            "deltatech_stock_inventory.group_view_inventory_button",
            "deltatech_stock_inventory.group_merge_inventory",
        ):
            group = env.ref(xmlid)
            admin.group_ids = [Command.link(group.id)]
            env.user.group_ids = [Command.link(group.id)]
        env.flush_all()

        chart = env["account.chart.template"].with_company(company)
        cls.acc_371 = chart.ref("pcg_371")
        cls.acc_607 = chart.ref("ro_pcg_expense")

        # depozitele: cel creat automat cu compania devine WH, plus un WH2 pentru defalcarea din kanban
        cls.wh = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        cls.wh.write({"name": "Depozit central", "code": "WH", "kanban_display_stock": "detailed"})
        cls.wh2 = env["stock.warehouse"].create({"name": "Depozit secundar", "code": "WH2", "company_id": company.id})
        cls.loc_wh = cls.wh.lot_stock_id
        cls.loc_wh2 = cls.wh2.lot_stock_id

        cls.categ = env["product.category"].create({"name": "Mărfuri"})
        cls.categ.with_company(company).write(
            {
                "property_cost_method": "fifo",
                "property_valuation": "real_time",
                "property_stock_valuation_account_id": cls.acc_371.id,
            }
        )

        def product(name, cost, price):
            return env["product.product"].create(
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

        cls.surub = product("Șurub M8", 2.0, 3.5)
        cls.vopsea = product("Vopsea albă 5L", 80.0, 119.0)
        cls.diblu = product("Diblu 8 mm", 0.5, 0.9)
        cls.cuie = product("Cuie 50 mm", 0.1, 0.2)

        # locația de ajustare: contul de pierderi dă contrapartida notei (607)
        cls.loc_adjust = cls.surub.with_company(company).property_stock_inventory
        cls.loc_adjust.valuation_account_id = cls.acc_607

        # stocul inițial vine din recepții de la furnizor, cu preț, ca straturile FIFO să aibă valoare
        supplier = env.ref("stock.stock_location_suppliers")
        for prod, qty, price, location in (
            (cls.surub, 100, 2.0, cls.loc_wh),
            (cls.vopsea, 20, 80.0, cls.loc_wh),
            (cls.diblu, 50, 0.5, cls.loc_wh),
            (cls.surub, 30, 2.0, cls.loc_wh2),
            (cls.cuie, 50, 0.1, cls.loc_wh2),
        ):
            move = env["stock.move"].create(
                {
                    "product_id": prod.id,
                    "uom_id": prod.uom_id.id,
                    "product_uom_qty": qty,
                    "price_unit": price,
                    "location_id": supplier.id,
                    "location_dest_id": location.id,
                    "company_id": company.id,
                }
            )
            move._action_confirm()
            move.quantity = qty
            move.picked = True
            move._action_done()

        # două inventare parțiale validate pe WH2, fără diferențe — materialul pentru unire
        cls.inv_rafturi = env["stock.inventory"]
        for name in ("Inventar raft A", "Inventar raft B"):
            inv = env["stock.inventory"].create(
                {"name": name, "location_ids": [Command.set(cls.loc_wh2.ids)], "company_id": company.id}
            )
            inv.action_start()
            inv.line_ids.is_ok = True
            inv.action_validate()
            cls.inv_rafturi |= inv

        # inventarul principal, în ciornă
        cls.inv = env["stock.inventory"].create(
            {
                "name": "Inventar anual depozit central",
                "location_ids": [Command.set(cls.loc_wh.ids)],
                "company_id": company.id,
                "date": fields.Datetime.now(),
            }
        )

        # asistentul „Confirmă inventar" deschide implicit locația principală a depozitului
        env["ir.default"].set(
            "stock.confirm.inventory", "location_id", cls.loc_wh.id, user_id=admin.id, company_id=company.id
        )

        # baza poate avea produse demo: le arhivăm, ca kanban-ul să arate doar produsele fluxului
        ours = (cls.surub | cls.vopsea | cls.diblu | cls.cuie).product_tmpl_id
        env["product.template"].sudo().search([("id", "not in", ours.ids)]).active = False

        cls.act_inventory = env.ref("deltatech_stock_inventory.action_inventory_form")
        cls.act_quants = env.ref("stock.action_view_inventory_tree")
        cls.act_wh_products = env.ref("deltatech_stock_inventory.action_product_template_warehouse")
        cls.act_products = env.ref("stock.product_template_action_product")

    def _form(self, record, name, **extra):
        shot = {
            "url": f"action={self.act_inventory.id}&id={record.id}&model=stock.inventory&view_type=form",
            "name": name,
            "wait": ".o_form_view",
            "settle": 2500,
            "full": True,
        }
        shot.update(extra)
        return shot

    def _capture(self, shots):
        self.env.flush_all()
        self.capture_screenshots(shots)
        self.env.invalidate_all()

    def test_capture_fise(self):
        inv = self.inv

        # Faza 1 — documentul în ciornă
        self._capture(
            [
                self._form(
                    inv,
                    "02_document_nou.png",
                    highlight=[
                        "div[name='location_ids']",
                        "div[name='prefill_counted_quantity']",
                        "button[name='action_start']",
                    ],
                ),
            ]
        )

        # Faza 2 — pornit: liniile generate din stoc
        inv.action_start()
        self._capture(
            [
                self._form(
                    inv,
                    "03_linii_generate.png",
                    click_btn="button[name='action_open_inventory_lines']",
                    wait_after=".o_list_view",
                ),
                # lista de numărare se tipărește înainte de numărare: coloana faptică e goală
                self.report_shot(REPORT_POSITION, inv, "04_lista_numarare_pdf.png"),
            ]
        )

        # Faza 3 — numărat: minus Șurub M8, plus Vopsea albă 5L, Diblu rămâne nenumărat
        lines = {line.product_id: line for line in inv.line_ids}
        lines[self.surub].write({"product_qty": 95, "is_ok": True})
        lines[self.vopsea].write({"product_qty": 22, "is_ok": True})
        self._capture(
            [
                self._form(
                    inv,
                    "05_linii_numarate.png",
                    click_btn="button[name='action_open_inventory_lines']",
                    wait_after=".o_list_view",
                ),
                self._form(
                    inv,
                    "06_valori_document.png",
                    highlight=[
                        "label[for^='total_diff_value']",
                        "button[name='action_new_for_not_ok']",
                        "button[name='action_validate']",
                    ],
                ),
            ]
        )

        # Faza 4 — linia nenumărată (Diblu) trece într-un inventar separat, apoi validare
        inv.action_new_for_not_ok()
        inv.action_validate()
        self.assertEqual(inv.state, "done")
        account_move = inv.move_ids.account_move_id
        self.assertTrue(account_move, "Validarea trebuia să genereze nota contabilă a diferențelor")
        self._capture(
            [
                self._form(inv, "07_inventar_validat.png", highlight=["label[for^='total_posted_value']"]),
                self._form(
                    inv,
                    "08_miscari_produs.png",
                    click_btn="button[name='action_view_related_move_lines']",
                    wait_after=".o_list_view",
                ),
                self.report_shot(REPORT_DIFF, inv, "09_diferente_pdf.png"),
                self.account_move_shot(account_move[:1], "10_nota_contabila.png"),
            ]
        )

        # Faza 5 — unire, ajustare rapidă cu motiv, confirmare stoc, kanban, reaprovizionare
        quant = self.env["stock.quant"].search(
            [("product_id", "=", self.cuie.id), ("location_id", "=", self.loc_wh2.id)], limit=1
        )
        quant.with_context(inventory_mode=True).write(
            {
                "inventory_quantity": 48,
                "inventory_quantity_set": True,
                "inventory_note": "2 buc deteriorate la descărcare",
            }
        )
        self._capture(
            [
                {
                    "url": f"action={self.act_inventory.id}&view_type=list",
                    "name": "11_unire_inventare.png",
                    "wait": ".o_list_view",
                    "eval": JS_ACTION_MENU % {"rows": "'Inventar raft'", "match": "/Unește|Merge/"},
                    "eval_wait": 1500,
                    "settle": 2000,
                },
                {
                    "url": f"action={self.act_quants.id}",
                    "name": "12_inventariere_fizica_nota.png",
                    "wait": ".o_list_view",
                    "settle": 2500,
                    "highlight": ["tr.o_data_row:has-text('Cuie') td[name='inventory_note']"],
                },
                {
                    "url": f"action={self.act_wh_products.id}&id={self.vopsea.product_tmpl_id.id}"
                    "&model=product.template&view_type=form",
                    "name": "13_confirmare_stoc.png",
                    "wait": ".o_form_view",
                    "click_btn": "button:has-text('Confirmă stoc')",
                    "wait_after": ".modal .o_form_view",
                    "settle": 2500,
                },
                {
                    "url": f"action={self.act_products.id}&view_type=kanban",
                    "name": "14_kanban_stoc_depozite.png",
                    "wait": ".o_kanban_view",
                    "settle": 2500,
                },
                {
                    "url": f"action={self.act_products.id}&id={self.vopsea.product_tmpl_id.id}"
                    "&model=product.template&view_type=form",
                    "name": "15_reaprovizionare_grupare.png",
                    "wait": ".o_form_view",
                    "eval": JS_ACTION_MENU % {"rows": "null", "match": "/Reaprovizionare|Replenish/"},
                    "eval_wait": 1500,
                    "settle": 2000,
                    "highlight": [".modal div[name='reference_id']"],
                },
            ]
        )

        # Faza 6 — lista documentelor, cu toate stările ajunse în flux
        self._capture(
            [
                {
                    "url": f"action={self.act_inventory.id}&view_type=list",
                    "name": "01_lista_documente.png",
                    "wait": ".o_list_view",
                    "settle": 2000,
                },
            ]
        )
