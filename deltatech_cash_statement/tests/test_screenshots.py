# Copyright (C) 2026 Terrabit
# License OPL-1 (https://www.odoo.com/documentation/user/legal/licenses/licenses.html)
#
# Capturi de ecran pentru fișa consultant „Solduri de casă și diferențe de casă" — generate în RO.
#
# Seedează trei registre de casă pe jurnalul „Casa în lei" (5311): al doilea are soldul inițial
# tastat greșit (6.000 în loc de 6.190), iar la inventarierea din 29.09 casiera găsește în casă
# cu 120 lei mai puțin decât soldul contabil.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i l10n_ro,deltatech_cash_statement,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import json
import unittest
from datetime import date

from odoo import Command
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

WIZARD_LABEL = "Actualizare solduri cash"

# Selectează în lista registrelor de casă rândurile cu numele date și deschide meniul Acțiuni.
JS_SELECT_AND_ACTIONS = """
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    for (const row of document.querySelectorAll('tr.o_data_row')) {
        if (NAMES.some((n) => row.textContent.includes(n))) {
            row.querySelector('.o_list_record_selector input').click();
            await sleep(300);
        }
    }
    await sleep(800);
    [...document.querySelectorAll('.o_cp_action_menus button')]
        .find((b) => b.querySelector('.fa-cog')).click();
    await sleep(900);
"""

JS_OPEN_WIZARD = """
    [...document.querySelectorAll('.o-dropdown-item')]
        .find((i) => i.textContent.includes(WIZARD)).click();
    await sleep(2000);
    // loc pentru bulinele numerotate ale evidențierii, ca să nu acopere prima cifră
    const style = document.createElement('style');
    style.textContent = ['balance_start', 'accounting_balance', 'counted_balance', 'difference',
        'date', 'counterpart_account_id', 'partner_id', 'label']
        .map((f) => `.modal div[name='${f}']`).join(', ') + ' { padding-left: 16px; }';
    document.head.appendChild(style);
"""

# Trece wizardul pe „Înregistrare diferență de casă" și completează soldul numărat.
JS_DIFFERENCE = """
    document.querySelectorAll(".modal div[name='mode'] input")[1].click();
    await sleep(1200);
    const setInput = async (selector, value) => {
        const input = document.querySelector(selector);
        input.focus();
        input.value = value;
        input.dispatchEvent(new Event('input', {bubbles: true}));
        input.dispatchEvent(new Event('change', {bubbles: true}));
        input.blur();
        await sleep(1200);
    };
    await setInput(".modal div[name='counted_balance'] input", COUNTED);
"""

# Alege o valoare într-un câmp many2one: tastează și ia prima propunere.
JS_MANY2ONE = """
    const pick = async (field, text) => {
        const input = document.querySelector(`.modal div[name='${field}'] input`);
        input.focus();
        input.value = text;
        input.dispatchEvent(new Event('input', {bubbles: true}));
        await sleep(1800);
        document.querySelector('.o-autocomplete--dropdown-item a, .o-autocomplete--dropdown-item')
            .dispatchEvent(new MouseEvent('click', {bubbles: true}));
        await sleep(1500);
    };
    await pick('counterpart_account_id', '4282');
    await pick('partner_id', 'Elena');
"""

# Panoul de previzualizare a atașamentului (PDF-ul registrului) și chatter-ul de sub formular
HIDE_PREVIEW = (
    "(() => { const s = document.createElement('style'); s.textContent = "
    "'.o_attachment_preview, .o-mail-Form-chatter, .o-mail-ChatterContainer { display: none !important; }';"
    " document.head.appendChild(s); })()"
)


def _js(body, **values):
    consts = "".join(f"const {key} = {json.dumps(value)};\n" for key, value in values.items())
    return (
        f"async () => {{\n{consts}try {{\n{body}\n}} catch (e) {{\n"
        "const d = document.createElement('div'); d.id = 'dbg_err'; d.textContent = 'JS ERR ' + e;"
        "d.style.cssText = 'position:fixed;top:0;left:0;z-index:9999;background:red;color:#fff';"
        "document.body.appendChild(d);\n}\n}"
    )


@tagged("-at_install", "post_install", "fise_screenshots")
class TestCashStatementScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_cash_statement"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Comerț SRL")
        env = cls.env
        company = env.company
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [(4, company.id)], "company_id": company.id, "name": "Maria Ionescu"})

        def account(code):
            return env["account.account"].search(
                [("code", "=like", code + "%"), ("company_ids", "in", company.ids)], order="code", limit=1
            )

        cls.journal = cls.company_data["default_journal_cash"]
        cls.journal.write(
            {
                "name": "Casa în lei",
                "profit_account_id": account("7588").id,
                "loss_account_id": account("6588").id,
            }
        )
        cls.account_4282 = account("4282")
        partner = env["res.partner"]
        client = partner.create({"name": "Alfa Distribuție SRL", "is_company": True})
        supplier = partner.create({"name": "Beta Papetărie SRL", "is_company": True})
        cls.cashier = partner.create({"name": "Elena Dumitrescu"})
        receivable = client.property_account_receivable_id
        payable = supplier.property_account_payable_id

        def register(day, lines):
            statement_lines = env["account.bank.statement.line"].create(
                [
                    {
                        "journal_id": cls.journal.id,
                        "date": day,
                        "payment_ref": ref,
                        "amount": amount,
                        "counterpart_account_id": counterpart.id,
                        "partner_id": line_partner.id,
                    }
                    for ref, amount, counterpart, line_partner in lines
                ]
            )
            return env["account.bank.statement"].create(
                {
                    "name": f"Registru de casă {day.strftime('%d.%m.%Y')}",
                    "line_ids": [Command.set(statement_lines.ids)],
                }
            )

        # 25.09: ridicare de numerar de la bancă (5311 = 581) și o încasare de la client (5311 = 4111)
        cls.reg1 = register(
            date(2026, 9, 25),
            [
                ("Ridicare numerar de la bancă, CEC nr. 15", 5000.0, account("581"), partner),
                ("Încasare factura FV 102", 1190.0, receivable, client),
            ],
        )
        # 26.09: plată furnizor (401 = 5311) și avans de trezorerie (542 = 5311)
        cls.reg2 = register(
            date(2026, 9, 26),
            [
                ("Plată factura 4471 — papetărie", -850.0, payable, supplier),
                ("Avans de trezorerie — deplasare Cluj", -500.0, account("542"), cls.cashier),
            ],
        )
        # 29.09: încasare de la client (5311 = 4111); ziua inventarierii casei
        cls.reg3 = register(
            date(2026, 9, 29),
            [("Încasare factura FV 108", 2380.0, receivable, client)],
        )
        cls.reg1.write({"balance_start": 0.0, "balance_end_real": 6190.0})
        # soldul inițial al registrului din 26.09 a fost tastat greșit: 6.000 în loc de 6.190
        cls.reg2.write({"balance_start": 6000.0, "balance_end_real": 4650.0})
        cls.reg3.write({"balance_start": 4650.0, "balance_end_real": 7030.0})

        cls.act_dashboard = env.ref("account.open_account_journal_dashboard_kanban").id
        cls.act_registers = env.ref("account.action_view_bank_statement_tree").id
        env.flush_all()

    def _wizard(self, statements, **values):
        wizard_model = self.env["account.cash.update.balances"].with_context(lang="ro_RO", active_ids=statements.ids)
        form = Form(wizard_model)
        for name, value in values.items():
            setattr(form, name, value)
        return form.save()

    def _list_url(self):
        return f"action={self.act_registers}&view_type=list"

    def test_capture_fise(self):
        names_align = [self.reg2.name, self.reg3.name]
        names_inventory = [self.reg3.name]
        self.capture_screenshots(
            [
                # 1. Tabloul de bord: meniul jurnalului de casă → „Registre de casă"
                {
                    "url": f"action={self.act_dashboard}",
                    "name": "01_tablou_registre_casa.png",
                    "wait": ".o_kanban_record",
                    "eval": _js(
                        """
                        const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
                        const card = [...document.querySelectorAll('.o_kanban_record')]
                            .find((c) => c.textContent.includes(JOURNAL));
                        card.scrollIntoView({block: 'center'});
                        card.querySelector('.o_dropdown_kanban .dropdown-toggle, .o_dropdown_kanban button')
                            .click();
                        await sleep(1000);
                        """,
                        JOURNAL=self.journal.name,
                    ),
                    "eval_wait": 1200,
                    "highlight": [".o-dropdown--menu a:has-text('Registre de casă')"],
                    "settle": 1500,
                },
                # 2. Lista registrelor de casă: selecția și meniul Acțiuni
                {
                    "url": self._list_url(),
                    "name": "02_lista_registre_actiune.png",
                    "wait": ".o_list_view .o_data_row",
                    "eval": _js(JS_SELECT_AND_ACTIONS, NAMES=names_align),
                    "eval_wait": 1000,
                    "highlight": [f".o-dropdown-item:has-text('{WIZARD_LABEL}')"],
                    "settle": 1500,
                },
                # 3. Wizardul în modul „Aliniere la soldul contabil"
                {
                    "url": self._list_url(),
                    "name": "03_aliniere_sold_contabil.png",
                    "wait": ".o_list_view .o_data_row",
                    "eval": _js(JS_SELECT_AND_ACTIONS + JS_OPEN_WIZARD, NAMES=names_align, WIZARD=WIZARD_LABEL),
                    "eval_wait": 1500,
                    "highlight": [
                        ".modal div[name='balance_start']",
                        ".modal div[name='accounting_balance']",
                        ".modal-footer button[name='do_update_balance']",
                    ],
                    "settle": 1500,
                },
            ]
        )
        # Aplică alinierea pe registrele din 26.09 și 29.09, ca în captura 03
        self._wizard(self.reg2 | self.reg3).do_update_balance()
        self.env.flush_all()

        counted = "4.720,00"
        self.capture_screenshots(
            [
                # 4. Lista după aliniere: soldurile se înlănțuie, rândurile nu mai sunt roșii
                {
                    "url": self._list_url(),
                    "name": "04_registre_aliniate.png",
                    "wait": ".o_list_view .o_data_row",
                    "settle": 1800,
                },
                # 5. Diferență de casă: minus de 120 lei, propus pe 6588
                {
                    "url": self._list_url(),
                    "name": "05_diferenta_casa_6588.png",
                    "wait": ".o_list_view .o_data_row",
                    "eval": _js(
                        JS_SELECT_AND_ACTIONS + JS_OPEN_WIZARD + JS_DIFFERENCE,
                        NAMES=names_inventory,
                        WIZARD=WIZARD_LABEL,
                        COUNTED=counted,
                    ),
                    "eval_wait": 1500,
                    "highlight": [
                        ".modal div[name='mode']",
                        ".modal div[name='counted_balance']",
                        ".modal div[name='difference']",
                        ".modal div[name='counterpart_account_id']",
                    ],
                    "settle": 1500,
                },
                # 6. Minusul imputat casierei: 4282 cu persoana responsabilă
                {
                    "url": self._list_url(),
                    "name": "06_diferenta_casa_4282.png",
                    "wait": ".o_list_view .o_data_row",
                    "eval": _js(
                        JS_SELECT_AND_ACTIONS + JS_OPEN_WIZARD + JS_DIFFERENCE + JS_MANY2ONE,
                        NAMES=names_inventory,
                        WIZARD=WIZARD_LABEL,
                        COUNTED=counted,
                    ),
                    "eval_wait": 1500,
                    "highlight": [
                        ".modal div[name='date']",
                        ".modal div[name='counterpart_account_id']",
                        ".modal div[name='partner_id']",
                        ".modal-footer button[name='do_update_balance']",
                    ],
                    "settle": 1500,
                },
                # 7. Blocaj: diferența datată înaintea registrului
                {
                    "url": self._list_url(),
                    "name": "07_eroare_data_anterioara.png",
                    "wait": ".o_list_view .o_data_row",
                    "eval": _js(
                        JS_SELECT_AND_ACTIONS
                        + JS_OPEN_WIZARD
                        + JS_DIFFERENCE
                        + JS_MANY2ONE
                        + """
                        // câmpul de dată e un buton până primește focus, apoi devine input
                        document.querySelector(".modal div[name='date'] button").focus();
                        await sleep(800);
                        const dateInput = document.querySelector(".modal div[name='date'] input");
                        dateInput.value = DAY;
                        dateInput.dispatchEvent(new Event('input', {bubbles: true}));
                        dateInput.dispatchEvent(new Event('change', {bubbles: true}));
                        dateInput.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
                        await sleep(1200);
                        document.querySelector(".modal-footer button[name='do_update_balance']").click();
                        await sleep(2500);
                        """,
                        NAMES=names_inventory,
                        WIZARD=WIZARD_LABEL,
                        COUNTED=counted,
                        DAY="28.09.2026",
                    ),
                    "eval_wait": 1500,
                    "settle": 1500,
                },
            ]
        )
        # Aplică diferența ca în captura 06: minus de 120 lei imputat casierei (4282 = 5311)
        self._wizard(
            self.reg3,
            mode="difference",
            counted_balance=4720.0,
            counterpart_account_id=self.account_4282,
            partner_id=self.cashier,
        ).do_update_balance()
        self.env.flush_all()
        line = self.reg3.line_ids.filtered(lambda st_line: st_line.amount == -120.0)
        self.assertEqual(len(line), 1)
        self.capture_screenshots(
            [
                # 8. Registrul din 29.09 cu linia de diferență
                {
                    "url": f"action={self.act_registers}&id={self.reg3.id}&model=account.bank.statement&view_type=form",
                    "name": "08_registru_cu_diferenta.png",
                    "wait": ".o_form_view",
                    "eval": HIDE_PREVIEW,
                    "settle": 2000,
                },
                # 9. Nota contabilă a diferenței: 4282 = 5311
                dict(self.account_move_shot(line.move_id, "09_nota_diferenta_4282.png"), eval=HIDE_PREVIEW),
            ]
        )
