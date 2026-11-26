# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Recepția livrărilor pe note de recepție" — generate în timpul
# testelor, pe compania „Demo Recepții SRL" în RON: în RO pentru fișă și în EN
# (static/description/en/) pentru readme/USAGE.md.
#
# Seed (un singur furnizor, ca notele să consume din aceleași cereri):
#   - o comandă mai veche trecută prin asistent, a cărei cerere „Doar RFQ" a fost apoi consumată
#     de două note confirmate (una normală, una cu „Ignoră cantitățile negăsite"), plus o notă
#     confirmată și anulată, care și-a restituit cantitatea;
#   - comanda din pașii 1-3, trecută prin asistent după note: formularul ei arată la fel ca înainte
#     (meniul Acțiune și asistentul), iar cererea ei „Doar RFQ" e încă neconsumată;
#   - o notă în ciornă cu restul cantităților și o notă cu o cantitate prea mare (eroarea).
#
# Rulare:
#   odoo-bin -c odoo.conf -d <db> -i deltatech_reception_note,l10n_ro,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# Deschide meniul „Acțiune" (rotița) din formularul comenzii.
OPEN_ACTION_MENU = """
    [...document.querySelectorAll('.o_cp_action_menus button')]
        .find((b) => b.querySelector('.fa-cog')).click();
"""

# Deschide meniul „Acțiune" și alege acțiunea (eticheta e în limba capturii), ca să apară asistentul.
OPEN_WIZARD = """
    new Promise((resolve) => {
        [...document.querySelectorAll('.o_cp_action_menus button')]
            .find((b) => b.querySelector('.fa-cog')).click();
        setTimeout(() => {
            [...document.querySelectorAll('.o-dropdown--menu .dropdown-item')]
                .find((i) => i.textContent.includes('%(label)s')).click();
            resolve();
        }, 800);
    })
"""

WIZARD_LABEL = {"ro_RO": "Creează RFQ", "en_US": "Create reception note"}


@tagged("-at_install", "post_install", "fise_screenshots")
class TestReceptionNoteScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_reception_note"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Recepții SRL")
        company = cls.env.company
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        for xmlid in ("purchase.group_purchase_manager", "stock.group_stock_manager"):
            group = env.ref(xmlid)
            env.user.group_ids = [Command.link(group.id)]
            admin.group_ids = [Command.link(group.id)]

        # nume în română pentru depozit și recepții (create înaintea limbii RO)
        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        warehouse.write({"name": "Depozit central", "code": "WH"})
        warehouse.in_type_id.name = "Recepții"
        warehouse.out_type_id.name = "Livrări"

        cls.vendor = env["res.partner"].create(
            {"name": "Distribuție Materiale SRL", "country_id": env.ref("base.ro").id, "company_id": company.id}
        )
        cls.cement = cls._product("Ciment Portland 40 kg", "CIM40", 32.0)
        cls.adhesive = cls._product("Adeziv gresie 25 kg", "ADZ25", 41.0)
        cls.putty = cls._product("Glet de finisaj 20 kg", "GLT20", 58.0)

        # 1. comanda trecută prin asistent; cererea ei „Doar RFQ" e consumată de notele de mai jos
        po_old = cls._order("normal", "OF-2026-118", [(cls.cement, 100), (cls.adhesive, 50)])
        po_old.button_confirm()
        cls.rfq_old = cls._create_note_from(po_old)

        # 2. nota recepționată normal și nota cu un produs care nu e pe nicio cerere (forțat)
        cls.note_done = cls._order("note", False, [(cls.cement, 60), (cls.adhesive, 20)], delivery_note_no="AV 4521")
        cls.note_done.button_confirm()
        cls.note_forced = cls._order("note", False, [(cls.putty, 10)], delivery_note_no="AV 4530")
        cls.note_forced.ignore_quantities = True
        # confirmată de admin, în română: mesajul din istoric se scrie în limba celui care confirmă
        cls.note_forced.with_user(admin).with_context(lang="ro_RO").button_confirm()

        # 2b. o notă confirmată greșit și anulată: cantitățile ei se întorc în prima cerere (pasul 10)
        cls.note_cancelled = cls._order("note", False, [(cls.cement, 15)], delivery_note_no="AV 4526")
        cls.note_cancelled.button_confirm()
        cls.note_cancelled.with_user(admin).with_context(lang="ro_RO").button_cancel()

        # 3. comanda din pașii 1-3, trecută prin asistent după note: cererea ei e încă neconsumată
        cls.po_open = cls._order("normal", "OF-2026-131", [(cls.cement, 80), (cls.adhesive, 40)])
        cls.po_open.button_confirm()
        cls.rfq_new = cls._create_note_from(cls.po_open)

        # 5. nota în ciornă, cu restul de pe prima cerere, și nota cu o cantitate prea mare
        cls.note_draft = cls._order("note", False, [(cls.cement, 40), (cls.adhesive, 30)], delivery_note_no="AV 4537")
        cls.note_too_much = cls._order("note", False, [(cls.cement, 200)], delivery_note_no="AV 4541")

        cls.action_orders = env.ref("purchase.purchase_form_action")
        cls.action_rfq = env.ref("purchase.purchase_rfq")
        cls.action_prepare = env.ref("deltatech_reception_note.prepare_reception_note_action")
        cls.action_to_arrive = env.ref("deltatech_reception_note.view_reception_assigned_action")
        env.flush_all()

    @classmethod
    def _product(cls, name, code, price):
        return cls.env["product.product"].create(
            {
                "name": name,
                "default_code": code,
                "is_storable": True,
                "standard_price": price,
                "company_id": cls.env.company.id,
            }
        )

    @classmethod
    def _order(cls, reception_type, partner_ref, lines, **extra):
        return cls.env["purchase.order"].create(
            {
                "partner_id": cls.vendor.id,
                "partner_ref": partner_ref,
                "reception_type": reception_type,
                "order_line": [
                    Command.create({"product_id": product.id, "product_qty": qty, "price_unit": product.standard_price})
                    for product, qty in lines
                ],
                **extra,
            }
        )

    @classmethod
    def _create_note_from(cls, purchase):
        before = cls.env["purchase.order"].search([("reception_type", "=", "rfq_only")])
        wizard = cls.env["reception.note.create"].create({})
        wizard.with_context(active_ids=purchase.ids).do_create_reception_note()
        return cls.env["purchase.order"].search([("reception_type", "=", "rfq_only")]) - before

    def _form(self, record, action=None):
        url = f"id={record.id}&model={record._name}&view_type=form"
        return f"action={action.id}&{url}" if action else url

    def _shots(self):
        return [
            # 1. comanda normală confirmată, cu meniul Acțiune deschis pe „Creează RFQ"
            {
                "url": self._form(self.po_open, self.action_orders),
                "name": "01_comanda_actiune_creeaza_rfq.png",
                "wait": ".o_form_view",
                "eval": OPEN_ACTION_MENU,
                "highlight": [
                    "div[name='reception_type']",
                    {
                        lang: f".o-dropdown--menu .dropdown-item:has-text('{label}')"
                        for lang, label in WIZARD_LABEL.items()
                    },
                ],
                "settle": 2000,
            },
            # 2. asistentul de confirmare
            {
                "url": self._form(self.po_open, self.action_orders),
                "name": "02_asistent_creeaza_rfq.png",
                "wait": ".o_form_view",
                "eval": {lang: OPEN_WIZARD % {"label": label} for lang, label in WIZARD_LABEL.items()},
                "eval_wait": 2500,
                "highlight": [".modal button[name='do_create_reception_note']"],
                "settle": 2000,
            },
            # 3. cererea „Doar RFQ" creată, trimisă, cu cantitățile încă nerecepționate
            {
                "url": self._form(self.rfq_new, self.action_rfq),
                "name": "03_cerere_doar_rfq.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='reception_type']", ".o_field_one2many th[data-name='product_qty']"],
                "settle": 2000,
            },
            # 4. nota de recepție în ciornă, din meniul Note recepție
            {
                "url": self._form(self.note_draft, self.action_prepare),
                "name": "04_nota_receptie_ciorna.png",
                "wait": ".o_form_view",
                "highlight": [
                    "div[name='reception_type']",
                    "div[name='delivery_note_no']",
                    "div[name='ignore_quantities']",
                    "button[name='button_confirm']",
                ],
                "settle": 2000,
            },
            # 5. confirmarea unei note cu mai mult decât e pe cereri: mesajul de blocare
            {
                "url": self._form(self.note_too_much, self.action_prepare),
                "name": "05_eroare_cantitate_negasita.png",
                "wait": ".o_form_view",
                "click_btn": "button[name='button_confirm']",
                "wait_after": ".o_form_view",
                "settle": 4000,
            },
            # 6. nota confirmată, cu recepția creată
            {
                "url": self._form(self.note_done),
                "name": "06_nota_confirmata.png",
                "wait": ".o_form_view",
                "highlight": [".o-form-buttonbox button[name='action_view_picking']"],
                "settle": 2000,
            },
            # 7. nota confirmată cu „Ignoră cantitățile negăsite": mesajul din istoric
            {
                "url": self._form(self.note_forced),
                "name": "07_nota_cantitati_fortate.png",
                "wait": ".o_form_view",
                "hide_chatter": False,
                "highlight": ["div[name='ignore_quantities']"],
                "settle": 2500,
            },
            # 8. prima cerere „Doar RFQ" după consumul notelor
            {
                "url": self._form(self.rfq_old, self.action_rfq),
                "name": "08_cerere_dupa_consum.png",
                "wait": ".o_form_view",
                "highlight": [".o_field_one2many th[data-name='product_qty']"],
                "settle": 2000,
            },
            # 9. Note recepție → Pe drum: recepțiile în starea Pregătit
            {
                "url": f"action={self.action_to_arrive.id}",
                "name": "09_receptii_pe_drum.png",
                "wait": ".o_list_view",
                "settle": 2000,
            },
            # 10. nota anulată: cantitățile s-au întors în cerere, butonul Setează ca ciornă
            {
                "url": self._form(self.note_cancelled),
                "name": "10_nota_anulata.png",
                "wait": ".o_form_view",
                "highlight": [".o_statusbar_status", "button[name='button_draft']"],
                "settle": 2500,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), hide_systray=True, lang="en_US")
