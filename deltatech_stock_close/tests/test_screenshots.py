# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Închiderea mișcărilor de stoc" — generate în timpul testelor,
# în limba RO (fișa) și EN (readme/USAGE.md).
#
# Fluxul: asistentul Închide mișcările de stoc până la sfârșitul anului trecut, lista mișcărilor
# cu coloana Evaluare activă, fișa de magazie cu Doar active bifat și rezultatul ei, comparat cu
# fișa completă (fără opțiune).
#
# Rulare (bază cu planul de conturi RO, ex. creată cu țara companiei România):
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_stock_close,deltatech_doc_screenshots \
#       --test-tags=/deltatech_stock_close:TestStockCloseScreenshots --stop-after-init
import unittest
from datetime import date, datetime

from odoo import Command, fields
from odoo.tests import tagged
from odoo.tools import SQL

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


# Deschide o acțiune ca dialog peste lista mișcărilor de stoc, ca la un clic din meniu.
DO_ACTION_JS = """
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const until = async (selector) => {
        for (let i = 0; i < 100 && !document.querySelector(selector); i++) {
            await sleep(100);
        }
        return document.querySelector(selector);
    };
    const actionService = odoo.__WOWL_DEBUG__.root.env.services.action;
    actionService.doAction(%s);
"""

# 1. asistentul Închide mișcările de stoc, cu data scrisă în câmp ca de un operator
SET_DATE_JS = """async () => {
    %s
    const input = await until(".modal-content div[name='date'] input");
    input.focus();
    input.value = "%s";
    input.dispatchEvent(new Event("input", {bubbles: true}));
    input.dispatchEvent(new Event("change", {bubbles: true}));
    input.dispatchEvent(new KeyboardEvent("keydown", {key: "Enter", bubbles: true}));
    await sleep(600);
    input.blur();
    document.querySelector(".modal-content .modal-body").click();
    await sleep(400);
}"""

# Coloana opțională Evaluare activă, afișată din meniul coloanelor listei.
SHOW_VALUATION_ACTIVE_JS = """async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    document.querySelector(".o_optional_columns_dropdown_toggle").closest("button").click();
    await sleep(600);
    const box = document.querySelector(".o-dropdown--menu input[name='l10n_ro_valuation_active']");
    if (box && !box.checked) {
        box.click();
        await sleep(800);
    }
    document.body.dispatchEvent(new KeyboardEvent("keydown", {key: "Escape", bubbles: true}));
    document.querySelector(".o_control_panel").click();
    await sleep(600);
}"""

# Fișa de magazie (asistentul) deschisă ca dialog, pe înregistrarea pregătită în seed.
OPEN_SHEET_JS = """async () => {
    %s
    await until(".modal-content div[name='only_active']");
    await sleep(500);
    document.activeElement.blur();
    document.querySelector(".modal-content .modal-title").click();
    await sleep(300);
}"""

# Fișa rulată cu Afișare fișă: rezultatul se deschide pe pivot, trecem pe listă.
SHOW_SHEET_JS = """async () => {
    %s
    (await until(".modal-content button[name='button_show_sheet']")).click();
    await until(".o_pivot_view");
    await sleep(800);
    document.querySelector(".o_switch_view.o_list").click();
    await until(".o_list_view .o_data_row");
    await sleep(800);
    // coloanele goale/dublate (Factura fiscală, Document) lasă loc antetelor cantităților
    const style = document.createElement("style");
    style.textContent = "th[data-name='invoice_id'], td[name='invoice_id'], th[data-name='document'], "
        + "td[name='document'] {display: none !important;} .o_list_table {table-layout: auto !important;}";
    document.head.appendChild(style);
    document.querySelectorAll(".o_list_table col").forEach((col) => (col.style.width = ""));
    document.querySelectorAll(".o_list_table th").forEach((th) => (th.style.width = ""));
    await sleep(500);
}"""


def _sheet_dialog(sheet, title):
    return DO_ACTION_JS % (
        f"{{name: '{title}', type: 'ir.actions.act_window', res_model: 'l10n.ro.stock.storage.sheet', "
        f"res_id: {sheet.id}, views: [[false, 'form']], target: 'new'}}"
    )


def _sheet_dialog_lang(sheet, js):
    """Același dialog în ambele limbi, cu titlul acțiunii din meniu."""
    titles = {"ro_RO": "Raport Fișă de magazie", "en_US": "Stock Sheet Report"}
    return {lang: js % _sheet_dialog(sheet, title) for lang, title in titles.items()}


@tagged("-at_install", "post_install", "fise_screenshots")
class TestStockCloseScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_stock_close"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.company = cls.prepare_ro_company()
        cls.env = cls.env(context=dict(cls.env.context, tz="Europe/Bucharest"))
        admin = cls.env.ref("base.user_admin")
        admin.write(
            {
                "tz": "Europe/Bucharest",
                "group_ids": [Command.link(cls.env.ref("stock.group_stock_manager").id)],
            }
        )
        # anul trecut e închis; anul curent e încă deschis
        cls.year = fields.Date.context_today(admin).year
        cls.closed_until = date(cls.year - 1, 12, 31)
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.company.id)], limit=1)
        cls.location = cls.warehouse.lot_stock_id
        cls.supplier = cls.env["res.partner"].create({"name": "Furnizor Demo Hârtie SRL", "is_company": True})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Hârtie copiator A4 (top 500 coli)",
                "default_code": "HART-A4",
                "type": "consu",
                "is_storable": True,
                "standard_price": 20.0,
            }
        )
        cls.product.product_tmpl_id.update_field_translations(
            "name", {"ro_RO": "Hârtie copiator A4 (top 500 coli)", "en_US": "A4 copy paper (500 sheets)"}
        )
        cls.stock_account = cls.env["account.account"].search(
            [("company_ids", "in", cls.company.ids), ("code", "=like", "371%")], limit=1
        )
        cls._receive(40, 20.0, datetime(cls.year - 1, 11, 18, 10, 0))
        cls._receive(25, 22.0, datetime(cls.year - 1, 12, 12, 10, 0))
        cls._receive(30, 24.0, datetime(cls.year, 1, 15, 10, 0))
        # fișa de magazie pe decembrie anul trecut – ianuarie anul curent, cu și fără opțiune
        sheet_vals = {
            "location_id": cls.location.id,
            "product_ids": [Command.set(cls.product.ids)],
            "date_from": date(cls.year - 1, 12, 1),
            "date_to": date(cls.year, 1, 31),
        }
        Sheet = cls.env["l10n.ro.stock.storage.sheet"]
        cls.sheet_active = Sheet.create(dict(sheet_vals, only_active=True))
        cls.sheet_full = Sheet.create(dict(sheet_vals, only_active=False))
        cls.env.flush_all()

    @classmethod
    def _receive(cls, qty, price, move_date):
        picking_type = cls.warehouse.in_type_id
        picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.supplier.id,
                "picking_type_id": picking_type.id,
                "location_id": cls.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": cls.location.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": qty,
                            "price_unit": price,
                            "location_id": cls.env.ref("stock.stock_location_suppliers").id,
                            "location_dest_id": cls.location.id,
                        }
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.move_ids.quantity = qty
        picking.move_ids.picked = True
        picking.with_context(skip_backorder=True).button_validate()
        cls.env.flush_all()
        # recepția datată în trecut: data mișcării, a liniilor și a transferului
        move = picking.move_ids
        cls.env.cr.execute(
            SQL(
                "UPDATE stock_move SET date = %s, l10n_ro_account_id = COALESCE(l10n_ro_account_id, %s) WHERE id = %s",
                move_date,
                cls.stock_account.id,
                move.id,
            )
        )
        cls.env.cr.execute(SQL("UPDATE stock_move_line SET date = %s WHERE move_id = %s", move_date, move.id))
        cls.env.cr.execute(
            SQL(
                "UPDATE stock_picking SET date_done = %s, scheduled_date = %s WHERE id = %s",
                move_date,
                move_date,
                picking.id,
            )
        )
        cls.env.invalidate_all()
        return move

    def _close_moves(self):
        wizard = self.env["stock.close.moves"].create({"date": self.closed_until})
        wizard.action_close()
        self.env.flush_all()

    def _moves_list(self):
        return f"action={self.env.ref('stock.stock_move_action').id}&view_type=list"

    def _sheet_shot(self, sheet, name):
        return {
            "url": self._moves_list(),
            "name": name,
            "wait": ".o_list_view .o_data_row",
            "eval": _sheet_dialog_lang(sheet, SHOW_SHEET_JS),
            "eval_wait": 1500,
            "settle": 1500,
        }

    def _shots_before(self):
        wizard_action = self.env.ref("deltatech_stock_close.action_stock_close_moves")
        open_wizard = DO_ACTION_JS % wizard_action.id
        closed = self.closed_until
        return [
            # 1. asistentul Închide mișcările de stoc, cu ultima zi a anului închis
            {
                "url": self._moves_list(),
                "name": "01_inchidere_miscari_asistent.png",
                "wait": ".o_list_view .o_data_row",
                "eval": {
                    "ro_RO": SET_DATE_JS % (open_wizard, closed.strftime("%d.%m.%Y")),
                    "en_US": SET_DATE_JS % (open_wizard, closed.strftime("%m/%d/%Y")),
                },
                "eval_wait": 1000,
                "highlight": [".modal-content div[name='date']", ".modal-footer button[name='action_close']"],
            },
        ]

    def _shots_after(self):
        return [
            # 2. lista mișcărilor de stoc: coloana Evaluare activă, oprită pe mișcările închise
            {
                "url": self._moves_list(),
                "name": "02_miscari_evaluare_activa.png",
                "wait": ".o_list_view .o_data_row",
                "eval": SHOW_VALUATION_ACTIVE_JS,
                "eval_wait": 1000,
                "highlight": ["th[data-name='l10n_ro_valuation_active']", "td[name='l10n_ro_valuation_active']"],
            },
            # 3. fișa de magazie cu opțiunea Doar active bifată
            {
                "url": self._moves_list(),
                "name": "03_fisa_magazie_doar_active.png",
                "wait": ".o_list_view .o_data_row",
                "eval": _sheet_dialog_lang(self.sheet_active, OPEN_SHEET_JS),
                "eval_wait": 1000,
                "highlight": [
                    ".modal-content div[name='only_active']",
                    ".modal-footer button[name='button_show_sheet']",
                ],
            },
            # 4. rezultatul: doar mișcările încă active
            self._sheet_shot(self.sheet_active, "04_fisa_magazie_rezultat_active.png"),
            # 5. aceeași fișă fără opțiune: toate mișcările, ca în localizarea românească
            self._sheet_shot(self.sheet_full, "05_fisa_magazie_completa.png"),
        ]

    def _capture(self, **kwargs):
        options = dict(viewport=(1920, 950), hide_systray=True, **kwargs)
        self.capture_screenshots(self._shots_before(), **options)
        self._close_moves()
        self.capture_screenshots(self._shots_after(), **options)

    def test_capture_fise(self):
        self._capture()

    def test_capture_usage(self):
        self._capture(lang="en_US")
