# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Găsirea și comasarea partenerilor duplicați" — generate
# în timpul testelor, în limba RO, pe compania „Demo Parteneri SRL" în RON.
#
# Seedează persoane fizice duplicate (același telefon scris diferit, același email cu
# litere diferite, nume asemănător la aceeași stradă), o familie cu același telefon fix
# (nu sunt dubluri), un telefon de centrală comun la 12 parteneri și două firme cu
# același CUI. Partea A: căutarea de dubluri, un grup, asistentul standard de îmbinare
# și lista grupurilor după o îmbinare și un „nu sunt dubluri". Partea B: lotul de
# comasare pe CUI, analizat, simulat, apoi aplicat și verificat.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_partner_merge,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPartnerMergeScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_partner_merge"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Parteneri SRL")
        company = cls.env.company
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        for xmlid in ("base.group_partner_manager", "deltatech_partner_merge.group_partner_merge_apply"):
            admin.group_ids = [Command.link(env.ref(xmlid).id)]
        ro = env.ref("base.ro")
        Partner = env["res.partner"]

        def partner(name, **vals):
            return Partner.create({"name": name, "country_id": ro.id, "company_id": company.id, **vals})

        # persoane fizice duplicate
        cls.ion_a = partner("Ion Popescu", phone="0722 913 456", city="București", street="Str. Fabricii nr. 3")
        cls.ion_b = partner("Popescu Ion", phone="+40 722 913 456", city="București")
        partner("Maria Ionescu", email="Maria.Ionescu@Example.com", city="Iași")
        partner("Maria Ionescu", email="maria.ionescu@example.com", phone="0745 118 220", city="Iași")
        street = {"city": "Cluj-Napoca", "zip": "400001"}
        partner("Gheorghe Vasilescu", street="Str. Lalelelor nr. 5", **street)
        partner("Gheorghe Vasilesc", street="Strada Lalelelor 5", **street)
        partner("Gheorghe Vasilescu", street="Str. Zorilor nr. 12", city="Cluj-Napoca", zip="400335")
        # o familie cu același telefon fix: nu sunt dubluri
        cls.andrei = partner("Andrei Marin", phone="0268 412 345", city="Brașov")
        cls.elena = partner("Elena Marin", phone="0268 412 345", city="Brașov")
        # adresa de facturare a unui client, cu emailul lui: nu e dublură
        beta = partner("Beta Distribuție SRL", email="office@beta-distributie.ro", is_company=True, vat="RO90000936")
        partner("Beta Distribuție – facturare", email="office@beta-distributie.ro", type="invoice", parent_id=beta.id)
        # un telefon de centrală comun prea multor parteneri
        for i in range(1, 13):
            partner(f"Client magazin {i:02d}", phone="0700 123 123", city="Constanța")
        # firme cu același CUI, pentru căutare și pentru lot
        cls.alfa = partner("Alfa Construct SRL", vat="RO90000910", is_company=True, city="Ploiești")
        partner("Alfa Construct S.R.L.", vat="RO 90000910", is_company=True, city="Ploiești")
        partner("Gamma Logistic SRL", vat="RO90000928", is_company=True, city="Pitești")
        partner("Gamma Logistic S.R.L.", vat="ro90000928", is_company=True, city="Pitești")
        # același CUI scris o dată fără prefixul RO: îl găsește căutarea, nu și lotul
        partner("Delta Agro SRL", vat="RO90000944", is_company=True, city="Craiova")
        partner("Delta Agro S.R.L.", vat="90000944", is_company=True, city="Craiova")
        # o factură postată pe una din fișele Alfa: grupul ajunge în categoria A
        invoice = cls.init_invoice("out_invoice", partner=cls.alfa, amounts=[1200.0], post=True)
        cls.invoice = invoice

        # partea A: o căutare în ciornă și una rulată
        Scan = env["partner.duplicate.scan"]
        cls.scan_draft = Scan.create({"name": "Curățenie parteneri magazin online"})
        cls.scan = Scan.create({"name": "Curățenie parteneri octombrie"})
        # motivele se scriu în limba utilizatorului care rulează căutarea
        cls.scan.with_context(lang="ro_RO").action_scan()
        cls.group_phone = cls.scan.group_ids.filtered(lambda g: cls.ion_a in g.partner_ids)
        cls.group_family = cls.scan.group_ids.filtered(lambda g: cls.andrei in g.partner_ids)
        cls.action_groups = env["ir.actions.act_window"].create(
            {
                "name": "Grupuri de dubluri",
                "res_model": "partner.duplicate.group",
                "view_mode": "list,form",
                "domain": [("scan_id", "=", cls.scan.id)],
            }
        )

        # partea B: un lot în ciornă și unul analizat
        Batch = env["partner.merge.batch"]
        cls.batch_draft = Batch.create({"name": "Comasare CUI — lot 2"})
        cls.batch = Batch.create({"name": "Comasare CUI — lot 1", "group_limit": 0, "archive_instead_of_delete": True})
        # indexurile pe cheile străine, create înaintea lotului, cum cere fișa
        cls.batch.action_create_indexes()
        cls.batch.with_context(lang="ro_RO").action_analyze()

    def _form(self, record):
        return f"id={record.id}&model={record._name}&view_type=form"

    def test_capture_fise(self):
        self.capture_screenshots(
            [
                # 1. căutarea nouă, cu criteriile
                {
                    "url": self._form(self.scan_draft),
                    "name": "01_cautare_dubluri_ciorna.png",
                    "wait": ".o_form_view",
                    "highlight": ["div[name='threshold']", "button[name='action_scan']"],
                    "settle": 2000,
                },
                # 2. căutarea rulată: rezultatul și grupurile cu scor și motiv
                {
                    "url": self._form(self.scan),
                    "name": "02_cautare_dubluri_grupuri.png",
                    "wait": ".o_form_view",
                    "settle": 2000,
                },
                # 3. raportul căutării, cu telefonul de centrală sărit
                {
                    "url": self._form(self.scan),
                    "name": "03_cautare_dubluri_raport.png",
                    "wait": ".o_form_view",
                    "click_tab": "Raport",
                    "settle": 2000,
                },
                # 4. un grup: scor, motive și partenerii
                {
                    "url": self._form(self.group_phone),
                    "name": "04_grup_dubluri.png",
                    "wait": ".o_form_view",
                    "highlight": ["button[name='action_merge']"],
                    "settle": 2000,
                },
                # 5. asistentul standard „Îmbină contacte", deschis din grup
                {
                    "url": self._form(self.group_phone),
                    "name": "05_asistent_imbinare.png",
                    "wait": ".o_form_view",
                    "click_btn": "button[name='action_merge']",
                    "wait_after": ".modal .o_form_view",
                    "highlight": [".modal div[name='dst_partner_id']", ".modal button[name='action_merge']"],
                    "settle": 2500,
                },
                # 7. lotul nou de comasare
                {
                    "url": self._form(self.batch_draft),
                    "name": "07_lot_comasare_ciorna.png",
                    "wait": ".o_form_view",
                    "highlight": ["div[name='category_ids']", "button[name='action_analyze']"],
                    "settle": 2000,
                },
                # 8. lotul analizat: grupurile pe CUI și fișa păstrată
                {
                    "url": self._form(self.batch),
                    "name": "08_lot_comasare_analizat.png",
                    "wait": ".o_form_view",
                    "highlight": ["button[name='action_simulate']"],
                    "settle": 2000,
                },
            ],
            viewport=(1920, 1150),
            hide_systray=True,
        )

        # îmbinarea grupului pe telefon și familia marcată „nu sunt dubluri"
        action = self.group_phone.action_merge()
        wizard = self.env[action["res_model"]].with_context(**action["context"]).create({})
        wizard.action_merge()
        self.group_family.action_ignore()
        self.scan.action_refresh()
        self.batch.with_context(lang="ro_RO").action_simulate()
        self.capture_screenshots(
            [
                # 6. lista grupurilor, cu stările lor
                {
                    "url": f"action={self.action_groups.id}",
                    "name": "06_grupuri_dubluri_lista.png",
                    "wait": ".o_list_view",
                    "settle": 2000,
                },
                # 9. raportul simulării
                {
                    "url": self._form(self.batch),
                    "name": "09_lot_comasare_simulare.png",
                    "wait": ".o_form_view",
                    "click_tab": "Raport",
                    "highlight": ["button[name='action_apply']"],
                    "settle": 2000,
                },
            ],
            hide_systray=True,
        )

        self.batch.with_context(lang="ro_RO").action_apply()
        self.batch.with_context(lang="ro_RO").action_verify()
        self.capture_screenshots(
            [
                # 10. raportul verificării după aplicare
                {
                    "url": self._form(self.batch),
                    "name": "10_lot_comasare_verificare.png",
                    "wait": ".o_form_view",
                    "click_tab": "Raport",
                    "settle": 2000,
                },
            ],
            hide_systray=True,
        )
