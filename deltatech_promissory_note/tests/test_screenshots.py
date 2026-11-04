# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Bilete la ordin" — generate în timpul testelor,
# în limba RO (fișa) și EN (readme/USAGE.md).
#
# Fluxul: lista biletelor la ordin, un bilet primit de la client, un bilet emis către
# furnizor și ultimul bilet al unui contract, încasat, cu notificarea din chatter.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_promissory_note,deltatech_doc_screenshots \
#       --test-tags=/deltatech_promissory_note:TestPromissoryNoteScreenshots --stop-after-init
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPromissoryNoteScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_promissory_note"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company()
        ron = cls.env["res.currency"].with_context(active_test=False).search([("name", "=", "RON")], limit=1)
        ron.active = True
        # ultimul bilet încasat notifică utilizatorii grupului: adminul îl primește
        cls.env.ref("base.user_admin").group_ids = [(4, cls.env.ref("deltatech_promissory_note.bo_notifications").id)]

        bank_bt = cls.env["res.bank"].create({"name": "Banca Transilvania", "bic": "BTRLRO22"})
        bank_bcr = cls.env["res.bank"].create({"name": "Banca Comercială Română", "bic": "RNCBROBU"})
        bank_ing = cls.env["res.bank"].create({"name": "ING Bank", "bic": "INGBROBU"})

        def partner(name, iban, bank):
            rec = cls.env["res.partner"].create(
                {"name": name, "is_company": True, "country_id": cls.env.ref("base.ro").id, "city": "București"}
            )
            cls.env["res.partner.bank"].create({"partner_id": rec.id, "acc_number": iban, "bank_id": bank.id})
            return rec

        cls.customer = partner("Alfa Distribuție SRL", "RO66BTRLRONCRT0123456701", bank_bt)
        cls.customer2 = partner("Beta Construct SRL", "RO12INGB0000999901234567", bank_ing)
        cls.vendor = partner("Gama Materiale SRL", "RO35RNCB0082001234560001", bank_bcr)
        company_iban = "RO49AAAA1B31007593840000"
        company_bank = cls.env["res.partner.bank"].search([("partner_id", "=", company.partner_id.id)], limit=1)
        if not company_bank:
            company_bank = cls.env["res.partner.bank"].create(
                {"partner_id": company.partner_id.id, "acc_number": company_iban, "bank_id": bank_bcr.id}
            )
        else:
            company_bank.bank_id = bank_bcr
        company_iban = company_bank.acc_number

        Note = cls.env["promissory.note"]

        def note(name, note_type, partner_rec, partner_bank, due, amount, agreement, **extra):
            if note_type == "customer":
                issuer, beneficiary = partner_rec, company.partner_id
                acc_i, bank_i = partner_rec.bank_ids[0].acc_number, partner_bank
                acc_b, bank_b = company_iban, bank_bcr
            else:
                issuer, beneficiary = company.partner_id, partner_rec
                acc_i, bank_i = company_iban, bank_bcr
                acc_b, bank_b = partner_rec.bank_ids[0].acc_number, partner_bank
            vals = {
                "name": name,
                "type": note_type,
                "agreement": agreement,
                "date_due": due,
                "amount": amount,
                "currency_id": ron.id,
                "issuer_id": issuer.id,
                "beneficiary_id": beneficiary.id,
                "acc_issuer": acc_i,
                "acc_beneficiary": acc_b,
                "bank_issuer_id": bank_i.id,
                "bank_beneficiary_id": bank_b.id,
            }
            vals.update(extra)
            return Note.create(vals)

        cls.note_cashed = note(
            "BTRL3AA 0012344",
            "customer",
            cls.customer,
            bank_bt,
            "2026-10-15",
            15000.0,
            "Contract 125/2026",
            cashed_amount=15000.0,
            cashed_date="2026-10-16",
        )
        cls.note_cashed.action_cashed()
        cls.note_customer = note(
            "BTRL3AA 0012345",
            "customer",
            cls.customer,
            bank_bt,
            "2026-11-15",
            15000.0,
            "Contract 125/2026",
            note="Bilet primit la livrarea din 15.09.2026; se depune la bancă la scadență.",
        )
        cls.note_last = note(
            "BTRL3AA 0012346",
            "customer",
            cls.customer,
            bank_bt,
            "2026-12-15",
            15000.0,
            "Contract 125/2026",
            is_last_bo=True,
        )
        cls.note_vendor = note(
            "RNCB3BB 0004521",
            "vendor",
            cls.vendor,
            bank_bcr,
            "2026-11-30",
            8250.0,
            "Contract furnizare 37/2026",
        )
        cls.note_cancel = note(
            "INGB3CC 0000781",
            "customer",
            cls.customer2,
            bank_ing,
            "2026-11-20",
            4300.0,
            "Comanda 2026/118",
        )
        cls.note_cancel.action_cancel()
        cls.env.flush_all()
        cls.action = cls.env.ref("deltatech_promissory_note.action_promissory_note")

    def _form(self, rec):
        return f"action={self.action.id}&id={rec.id}&model=promissory.note&view_type=form"

    def _shots_before(self):
        return [
            # 1. lista biletelor la ordin
            {
                "url": f"action={self.action.id}&view_type=list",
                "name": "01_lista_bilete.png",
                "wait": ".o_list_view",
                "highlight": ["th[data-name='date_due']", "th[data-name='state']"],
            },
            # 2. bilet primit de la client: emitent = clientul, beneficiar = compania
            {
                "url": self._form(self.note_customer),
                "name": "02_bilet_client.png",
                "wait": ".o_form_view",
                "highlight": [
                    "div[name='type']",
                    "div[name='issuer_id']",
                    "div[name='beneficiary_id']",
                    "div[name='bank_issuer_id']",
                    "button[name='action_cashed']",
                ],
            },
            # 3. bilet emis către furnizor: emitent = compania
            {
                "url": self._form(self.note_vendor),
                "name": "03_bilet_furnizor.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='type']", "div[name='issuer_id']", "div[name='beneficiary_id']"],
            },
        ]

    def _shots_after(self):
        return [
            # 4. ultimul bilet al contractului, încasat: notificarea în chatter
            {
                "url": self._form(self.note_last),
                "name": "04_ultimul_bilet_incasat.png",
                "wait": ".o-mail-Message",
                "hide_chatter": False,
                "settle": 2500,
                "highlight": {
                    lang: [
                        "div[name='cashed_amount']",
                        "div[name='is_last_bo']",
                        ".o_statusbar_status",
                        f".o-mail-Message-body:has-text('{text}')",
                    ]
                    for lang, text in (("ro_RO", "Ultimul bilet la ordin"), ("en_US", "The last promissory"))
                },
            },
        ]

    def _capture(self, lang="ro_RO"):
        self.capture_screenshots(self._shots_before(), viewport=(1920, 1000), hide_systray=True, lang=lang)
        self.note_last.write({"cashed_amount": 15000.0, "cashed_date": "2026-12-16"})
        self.note_last.with_context(lang=lang).action_cashed()
        self.env.flush_all()
        self.assertEqual(self.note_last.state, "cashed")
        self.capture_screenshots(self._shots_after(), viewport=(1920, 1000), hide_systray=True, lang=lang)

    def test_capture_fise(self):
        self._capture()

    def test_capture_usage(self):
        self._capture(lang="en_US")
