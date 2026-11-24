# Copyright (C) 2026 Terrabit
# License OPL-1 (https://www.odoo.com/documentation/user/legal/licenses/licenses.html)
#
# Capturi de ecran pentru fișa consultant „Registrul de intrări-ieșiri" — RO pentru fișă,
# EN (static/description/en/) pentru readme/USAGE.md.
#
# Seedează câteva înregistrări datate crescător în anul curent, o rezervare, o înregistrare cu
# legături și una anulată.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_ledger,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest
from datetime import date

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# completează motivul în fereastra de anulare
JS_FILL_REASON_TPL = """async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    document.querySelector("button[name='action_cancel_wizard']").click();
    for (let i = 0; i < 40 && !document.querySelector(".modal div[name='reason'] textarea"); i++) {
        await sleep(250);
    }
    const area = document.querySelector(".modal div[name='reason'] textarea");
    area.value = 'REASON_TEXT';
    area.dispatchEvent(new Event('input', {bubbles: true}));
    await sleep(600);
}"""

JS_FILL_REASON = {
    "ro_RO": JS_FILL_REASON_TPL.replace("REASON_TEXT", "Document înregistrat din greșeală"),
    "en_US": JS_FILL_REASON_TPL.replace("REASON_TEXT", "Document registered by mistake"),
}


@tagged("-at_install", "post_install", "fise_screenshots")
class TestLedgerScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_ledger"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        year = date.today().year
        Ledger = cls.env["ledger.ledger"]
        partners = cls.env["res.partner"].create(
            [
                {"name": "Ferma Verde SRL"},
                {"name": "Primăria Municipiului Exemplu"},
                {"name": "Construct Nord SA"},
            ]
        )
        rows = [
            ("entry", date(year, 1, 12), "FV 112", partners[0], "Cluj-Napoca", "Factură furnizor"),
            ("exit", date(year, 2, 3), "OF 7", partners[2], "Sediu", "Ofertă de preț"),
            ("entry", date(year, 3, 18), "ADR 55", partners[1], "Primărie", "Adresă autorizație"),
        ]
        cls.records = Ledger
        for rtype, rdate, docno, partner, origin, descr in rows:
            cls.records |= Ledger.create(
                {
                    "record_type": rtype,
                    "record_date": rdate,
                    "document_number": docno,
                    "contact_id": partner.id,
                    "place_of_origin": origin,
                    "record_short_description": descr,
                }
            )
        cls.active = cls.records[-1]
        cls.reserved = Ledger.with_context(default_state="reserved").create(
            {"record_type": "exit", "state": "reserved"}
        )
        cls.canceled = Ledger.create(
            {
                "record_type": "entry",
                "record_date": date(year, 3, 20),
                "document_number": "FV 999",
                "contact_id": partners[0].id,
                "record_short_description": "Introdusă greșit",
            }
        )
        cls.env["ledger.cancel.wizard"].create(
            {"ledger_ids": [(6, 0, cls.canceled.ids)], "reason": "Document înregistrat din greșeală"}
        ).action_cancel()
        cls.records |= cls.reserved | cls.canceled
        cls.link_record = cls.records[0]
        cls.env["ledger.link"].create(
            [
                {"ledger_id": cls.link_record.id, "link_type": "url", "url": "https://www.terrabit.ro"},
            ]
        )
        if "project.project" in cls.env:
            project = cls.env["project.project"].create({"name": "Reamenajare sediu"})
            cls.env["ledger.link"].create(
                {
                    "ledger_id": cls.link_record.id,
                    "link_type": "record",
                    "reference": f"project.project,{project.id}",
                }
            )
        cls.action = cls.env.ref("deltatech_ledger.action_ledger_model")
        cls.menu = cls.env.ref("deltatech_ledger.menu_ledger_model")
        cls.print_action = cls.env.ref("deltatech_ledger.action_ledger_report_wizard", raise_if_not_found=False)

    def _form(self, rec):
        return f"id={rec.id}&model=ledger.ledger&view_type=form&menu_id={self.menu.id}"

    def _shots(self):
        report_ids = ",".join(str(i) for i in self.records.sorted("name").ids)
        shots = [
            {
                "url": f"action={self.action.id}&menu_id={self.menu.id}&view_type=list",
                "name": "01_lista_registru.png",
                "wait": ".o_list_view",
            },
            {
                "url": self._form(self.active),
                "name": "02_inregistrare_noua.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='record_type']", "div[name='document_number']", "div[name='contact_id']"],
            },
            {
                "url": self._form(self.reserved),
                "name": "03_rezervare.png",
                "wait": ".o_form_view",
                "highlight": ["button[name='action_confirm']"],
            },
            {
                "url": self._form(self.link_record),
                "name": "04_legaturi.png",
                "wait": ".o_form_view",
                "click_tab": {"ro_RO": "Legături", "en_US": "Links"},
                "highlight": [".o_field_widget[name='link_ids']"],
            },
            {
                "url": self._form(self.active),
                "name": "05_anulare.png",
                "wait": ".o_form_view",
                "eval": JS_FILL_REASON,
                "highlight": [".modal div[name='reason']"],
            },
            {"url": self._form(self.canceled), "name": "06_inregistrare_anulata.png", "wait": ".o_form_view"},
        ]
        if self.print_action:
            shots.append(
                {
                    "url": f"action={self.print_action.id}&menu_id={self.menu.id}",
                    "name": "07_tiparire.png",
                    "wait": ".modal",
                }
            )
        shots.append(self.report_shot("deltatech_ledger.report_ledger_document", report_ids, "08_raport_pdf.png"))
        return shots

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")

    def _spare_record(self):
        # each GIF cancels its own record, so the two languages do not meet a canceled one
        return self.env["ledger.ledger"].create(
            {
                "record_type": "entry",
                "record_date": date.today(),
                "document_number": "FV 130",
                "contact_id": self.active.contact_id.id,
                "record_short_description": "Factură furnizor",
            }
        )

    def _gif_steps(self):
        return [
            {"goto": f"id={self._spare_record().id}&model=ledger.ledger&view_type=form&menu_id={self.menu.id}"},
            {
                "caption": {
                    "ro_RO": "Un document înregistrat greșit nu se șterge",
                    "en_US": "A record entered by mistake is never deleted",
                }
            },
            {"click": "button[name='action_cancel_wizard']", "wait_after": ".modal"},
            {"caption": {"ro_RO": "Se anulează, cu un motiv", "en_US": "It is canceled, with a reason"}},
            {
                "type": {"ro_RO": "Document înregistrat din greșeală", "en_US": "Document registered by mistake"},
                "into": "reason",
            },
            {"click": ".modal button[name='action_cancel']", "wait_after": ".o_form_view"},
            {
                "caption": {
                    "ro_RO": "Numărul rămâne în registru, fără goluri",
                    "en_US": "The number stays in the register, no gaps",
                },
                "hold": 2500,
            },
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_gif(self):
        self.capture_gif(self._gif_steps(), lang="en_US")
