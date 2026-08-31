# © 2026 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa consultant a modulului — generate în timpul testelor, în RO.
#
# Acoperă cele două ecrane care lipseau din fișă:
#   - previzualizarea cu o linie GALBENĂ (produs găsit doar după nume) — cazul pentru care
#     nu exista exemplu pe staging; seedăm aici toate trei culorile în același tabel, ca
#     fișa să poată arăta legenda completă într-o singură captură;
#   - activitatea „Import SPV necesită verificare" + nota colorată din chatter (19.0.1.4.0),
#     comportament care nu există în nicio bază locală, deci nu putea fi pozat manual.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_purchase_ubl,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest
from base64 import b64encode

from odoo import Command
from odoo.tests import tagged

from .test_process_attachments import _xml_invoice

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPurchaseUblScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_purchase_ubl"

    @classmethod
    def setUpClass(cls):
        # `l10n_ro_doc_screenshots` trăiește în repo-ul l10n_ro_ent și lipsește adesea din
        # CI-ul suitei deltatech: fără garda asta clasa cade pe `object` și setUpClass
        # crapă pe `prepare_ro_company`.
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        # Capturile se fac pe **compania demo a localizării RO** (`base.demo_company_ro`,
        # „RO Company" în RON, cu plan de conturi RO). Nu pe compania principală: aceea e
        # în USD și moneda nu mai poate fi schimbată o dată ce există note contabile
        # („You cannot change the currency of the company since some journal items already
        # exist") — `prepare_ro_company` înghite acea eroare, iar capturile ieșeau în $.
        company = cls.prepare_demo_company()
        # `cls.env` rulează ca superuser, a cărui companie rămâne cea principală: fără
        # rescrierea contextului, înregistrările seedate ar cădea pe compania greșită.
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=[company.id], lang="ro_RO"))
        # Compania demo RO nu are depozit (spre deosebire de compania principală), iar fără
        # el `purchase.order.picking_type_id` rămâne null și `create` cade pe constrângerea
        # NOT NULL din bază.
        if not cls.env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1):
            cls.env["stock.warehouse"].create({"name": "Depozit Central", "code": "DPC", "company_id": company.id})

        env = cls.env
        cls.vendor = env["res.partner"].create(
            {
                "name": "Furnizor Materiale SRL",
                "is_company": True,
                "vat": "RO12345674",
                "supplier_rank": 1,
                "country_id": env.ref("base.ro").id,
            }
        )

        # VERDE — produs cu cod de furnizor: potrivire sigură.
        cls.prod_green = env["product.product"].create({"name": "Cot PVC 110 mm", "type": "consu"})
        env["product.supplierinfo"].create(
            {
                "partner_id": cls.vendor.id,
                "product_tmpl_id": cls.prod_green.product_tmpl_id.id,
                "product_id": cls.prod_green.id,
                "product_code": "FM-COT-110",
                "price": 12.50,
            }
        )

        # GALBEN — produs al cărui NUME coincide exact cu descrierea din factură, dar
        # fără cod de furnizor și fără cod de bare: matcherul cade pe potrivirea după nume.
        # Numele trebuie să fie UNIC în bază — `_match_product_detailed` acceptă potrivirea
        # după nume doar la un singur rezultat (`len(products) == 1`).
        cls.prod_yellow = env["product.product"].create({"name": "Teu PVC 110 x 50 mm", "type": "consu"})

        cls.xml_preview = _xml_invoice(
            invoice_id="FMS-2026-00418",
            order_ref="PO-DEMO-UBL",
            supplier_vat="12345674",
            supplier_name="Furnizor Materiale SRL",
            lines=[
                {
                    "code": "FM-COT-110",
                    "name": "Cot PVC 110 mm",
                    "qty": "40",
                    "price": "12.50",
                    "line_total": "500.00",
                    "tax": "21",
                },
                {
                    # fără cod de furnizor → matcherul ajunge la potrivirea după nume (GALBEN)
                    "code": "",
                    "name": "Teu PVC 110 x 50 mm",
                    "qty": "15",
                    "price": "18.00",
                    "line_total": "270.00",
                    "tax": "21",
                },
                {
                    # nici cod, nici nume cunoscut → nicio potrivire (ROȘU)
                    "code": "FM-RED-063",
                    "name": "Reductie PVC 110/63 mm",
                    "qty": "8",
                    "price": "9.20",
                    "line_total": "73.60",
                    "tax": "21",
                },
            ],
        )

        # Comanda rămâne FĂRĂ linii, intenționat. `action_preview` restrânge potrivirea la
        # produsele de pe comandă (`_match_product_on_order_detailed`) când comanda are deja
        # linii — acolo cazul „potrivire doar după nume" nu poate apărea deloc. Potrivirea
        # completă (cod → nume → variante de nume) rulează doar pe o comandă goală, care e și
        # scenariul real al fișei: comandă creată din mesajul SPV, fără linii.
        cls.po_preview = env["purchase.order"].create(
            {
                "partner_id": cls.vendor.id,
                "company_id": company.id,
                "partner_ref": "PO-DEMO-UBL",
            }
        )

        # Wizardul în starea „preview": exact ecranul pe care îl vede operatorul după
        # ce apasă Preview, cu cele trei culori în tabel.
        cls.wizard = (
            env["purchase.ubl.import.wizard"]
            .with_context(active_model="purchase.order", active_id=cls.po_preview.id)
            .create(
                {
                    "data_file": b64encode(cls.xml_preview),
                    "filename": "FMS-2026-00418.xml",
                    "order_id": cls.po_preview.id,
                }
            )
        )
        cls.wizard.action_preview()

        # --- Scenariul activității (19.0.1.4.0) -------------------------------------
        # Comandă creată „din mesajul SPV": XML cu o linie pe care matcherul nu o poate
        # plasa, importată headless cu `purchase_ubl_no_new_products` — exact fluxul
        # automat. Rezultatul: notă colorată în chatter + activitate de verificare.
        cls.po_activity = env["purchase.order"].create(
            {
                "partner_id": cls.vendor.id,
                "company_id": company.id,
                "partner_ref": "PO-DEMO-SPV",
                "user_id": env.ref("base.user_admin").id,
                "order_line": [
                    Command.create({"product_id": cls.prod_green.id, "product_qty": 40, "price_unit": 12.50})
                ],
            }
        )
        xml_activity = _xml_invoice(
            invoice_id="FMS-2026-00419",
            order_ref="PO-DEMO-SPV",
            supplier_vat="12345674",
            supplier_name="Furnizor Materiale SRL",
            lines=[
                {
                    "code": "FM-NECUNOSCUT-01",
                    "name": "Racord flexibil 3/4 inch",
                    "qty": "6",
                    "price": "24.00",
                    "line_total": "144.00",
                    "tax": "21",
                }
            ],
        )
        att = env["ir.attachment"].create(
            {
                "name": "FMS-2026-00419.xml",
                "datas": b64encode(xml_activity),
                "mimetype": "application/xml",
                "res_model": "purchase.order",
                "res_id": cls.po_activity.id,
            }
        )
        env["ir.config_parameter"].sudo().set_param("deltatech_purchase_ubl.auto_import", "True")
        cls.po_activity.with_context(purchase_ubl_no_new_products=True)._process_attachments_for_post([], [att.id], {})
        cls.env.flush_all()

    def test_capture_fise(self):
        # Garda de seed: dacă scenariile nu s-au construit, capturile ar arăta ecrane
        # goale, iar fișa ar promite ce nu se vede. Mai bine picăm aici.
        self.assertEqual(
            self.wizard.line_ids.filtered(lambda l: l.match_type == "name").mapped("name"),
            ["Teu PVC 110 x 50 mm"],
            "Seed-ul trebuie să producă exact o linie GALBENĂ (potrivire după nume)",
        )
        self.assertTrue(
            self.po_activity.activity_ids.filtered(
                lambda a: a.summary in ("Import SPV necesită verificare", "SPV import needs review")
            ),
            "Seed-ul trebuie să producă activitatea de verificare pe comandă",
        )
        self.assertEqual(self.po_activity.currency_id.name, "RON", "Capturile trebuie să iasă în RON, nu în USD")

        self.capture_screenshots(
            [
                # Previzualizarea cu toate trei culorile; bulina ① indică linia galbenă.
                {
                    "url": f"id={self.wizard.id}&model=purchase.ubl.import.wizard&view_type=form",
                    "name": "06_preview_linie_galbena.png",
                    "wait": ".o_list_view",
                    "highlight": ["tr.o_data_row:has-text('Teu PVC 110 x 50 mm')"],
                    "settle": 2500,
                    "full": True,
                },
                # Comanda din fluxul automat: nota colorată + activitatea de verificare.
                {
                    "url": f"id={self.po_activity.id}&model=purchase.order&view_type=form",
                    "name": "07_activitate_verificare.png",
                    "wait": ".o_form_view",
                    # `hide_chatter` e True IMPLICIT în mixin: fără asta captura ieșea
                    # fără nota colorată și fără activitate — exact ce trebuie să arate.
                    "hide_chatter": False,
                    "highlight": [".o-mail-Chatter"],
                    "settle": 4000,
                    "full": True,
                },
            ],
            viewport=(1700, 1100),
        )
