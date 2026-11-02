# © 2026 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa consultant a modulului — generate în timpul testelor, în RO.
#
# Acoperă toți pașii fișei (1–7); capturile 06 și 07 sunt cele două ecrane care nu puteau
# fi pozate manual:
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
import logging
import unittest

from odoo import Command
from odoo.tests import tagged
from odoo.tools.binary import BinaryBytes

from .test_process_attachments import _xml_invoice as _base_xml_invoice


def _xml_invoice(**kwargs):
    """Factura de test cu date din 2026: TVA 21% e cota în vigoare abia din 1 august 2025,
    iar exemplele din fișă trebuie să arate o cotă corectă la data facturii."""
    xml = _base_xml_invoice(**kwargs)
    return (
        xml.replace(b"2025-01-01", b"2026-10-26").replace(b"2025-01-30", b"2026-11-25")
        if isinstance(xml, bytes)
        else xml.replace("2025-01-01", "2026-10-26").replace("2025-01-30", "2026-11-25")
    )


_logger = logging.getLogger(__name__)

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
        # `activate_ro_lang` înghite erorile; aici activăm limba explicit, ca să nu cădem
        # mai târziu pe „Invalid language code: ro_RO" la rescrierea contextului.
        cls.env["res.lang"]._activate_lang("ro_RO")
        cls.activate_ro_lang()
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
                    "name": "Reducție PVC 110/63 mm",
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

        # XML-ul atașat pe comandă: asistentul îl preia singur în **Fișier XML** când se
        # deschide din butonul **Importă UBL** (pașii 1–3 se pozează pe ecranele reale).
        env["ir.attachment"].create(
            {
                "name": "FMS-2026-00418.xml",
                "raw": cls.xml_preview,
                "mimetype": "application/xml",
                "res_model": "purchase.order",
                "res_id": cls.po_preview.id,
            }
        )

        # Wizardul în starea „preview": exact ecranul pe care îl vede operatorul după
        # ce apasă Preview, cu cele trei culori în tabel.
        cls.wizard = (
            env["purchase.ubl.import.wizard"]
            .with_context(active_model="purchase.order", active_id=cls.po_preview.id)
            .create(
                {
                    "data_file": BinaryBytes(cls.xml_preview),
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
                "raw": xml_activity,
                "mimetype": "application/xml",
                "res_model": "purchase.order",
                "res_id": cls.po_activity.id,
            }
        )

        # --- Scenariul „comandă confirmată" (pașii 4–6) ------------------------------
        # Marfă stocabilă cu evaluare perpetuă („la facturare" în Odoo 20), ca factura să
        # producă nota de stoc. Contul de stoc 371 „Mărfuri" se setează explicit pe categorie
        # (implicit planul RO folosește 301). Codurile din planul RO au 6 cifre (371000).
        acc = env["account.account"]
        cls.acc_371 = acc.search([("code", "=like", "371%"), ("company_ids", "in", company.id)], limit=1)
        assert cls.acc_371, "Contul 371 lipsește din planul de conturi al companiei demo RO"
        cls.categ_marfa = env["product.category"].create(
            {
                "name": "Mărfuri",
                "property_valuation": "real_time",
                "property_cost_method": "fifo",
                "property_stock_valuation_account_id": cls.acc_371.id,
            }
        )
        flow_products = env["product.product"]
        flow_lines = []
        xml_lines = []
        for name, code, qty, price in (
            ("Mufă PVC 110 mm", "FM-MUF-110", 20, 8.00),
            ("Colier metalic 110 mm", "FM-COL-110", 30, 4.50),
        ):
            product = env["product.product"].create(
                {"name": name, "type": "consu", "is_storable": True, "categ_id": cls.categ_marfa.id}
            )
            env["product.supplierinfo"].create(
                {
                    "partner_id": cls.vendor.id,
                    "product_tmpl_id": product.product_tmpl_id.id,
                    "product_id": product.id,
                    "product_code": code,
                    "price": price,
                }
            )
            flow_products |= product
            flow_lines.append(Command.create({"product_id": product.id, "product_qty": qty, "price_unit": price}))
            xml_lines.append(
                {
                    "code": code,
                    "name": name,
                    "qty": str(qty),
                    "price": f"{price:.2f}",
                    "line_total": f"{qty * price:.2f}",
                    "tax": "21",
                }
            )
        cls.po_flow = env["purchase.order"].create(
            {
                "partner_id": cls.vendor.id,
                "company_id": company.id,
                "partner_ref": "PO-DEMO-FLUX",
                "order_line": flow_lines,
            }
        )
        cls.po_flow.button_confirm()
        env["ir.attachment"].create(
            {
                "name": "FMS-2026-00420.xml",
                "raw": _xml_invoice(
                    invoice_id="FMS-2026-00420",
                    order_ref="PO-DEMO-FLUX",
                    supplier_vat="12345674",
                    supplier_name="Furnizor Materiale SRL",
                    lines=xml_lines,
                ),
                "mimetype": "application/xml",
                "res_model": "purchase.order",
                "res_id": cls.po_flow.id,
            }
        )

        env["ir.config_parameter"].sudo().set_bool("deltatech_purchase_ubl.auto_import", True)
        cls.po_activity.with_context(purchase_ubl_no_new_products=True)._process_attachments_for_post([], [att.id], {})
        cls.env.flush_all()

    def _form_url(self, action_xmlid, record):
        """Formularul unei înregistrări deschis prin acțiunea meniului: fără acțiune,
        breadcrumb-ul arată chip-ul „Nou(ă)" chiar și pe un document existent."""
        action = self.env.ref(action_xmlid)
        return f"action={action.id}&id={record.id}&model={record._name}&view_type=form"

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

        # Pașii 1–3 pe comanda fără linii (cazul galben); asistentul se deschide din butonul
        # real al comenzii, iar starea „previzualizare" se obține prin click pe butonul
        # **Previzualizare**, ca pe ecranul operatorului.
        open_wizard = {"click_btn": "button:has-text('Importă UBL')", "wait_after": ".modal-footer"}
        widen = (
            "const d = document.querySelector('.modal-dialog'); d.style.maxWidth = '1500px'; d.style.width = '95vw';"
        )
        click_preview = (
            "const sleep = ms => new Promise(r => setTimeout(r, ms));"
            "document.querySelector(\".modal-footer button[name='action_preview']\").click();"
            "await sleep(3000);"
        )
        self.capture_screenshots(
            [
                # Pasul 1: butonul de pe comandă.
                {
                    "url": self._form_url("purchase.purchase_rfq", self.po_preview),
                    "name": "01_buton_importa_ubl.png",
                    "wait": ".o_form_view",
                    "highlight": ["button:has-text('Importă UBL')"],
                    "settle": 2000,
                },
                # Pasul 2: asistentul cu fișierul preluat de pe comandă și cele trei opțiuni.
                {
                    "url": self._form_url("purchase.purchase_rfq", self.po_preview),
                    "name": "02_asistent_optiuni.png",
                    "wait": ".o_form_view",
                    **open_wizard,
                    "eval": "() => {" + widen + "}",
                    "highlight": [
                        ".modal div[name='data_file']",
                        ".modal div[name='update_prices']",
                        ".modal div[name='create_bill']",
                        ".modal div[name='validate_receipt']",
                    ],
                    "settle": 2000,
                },
                # Pasul 3: previzualizarea cu toate trei culorile; bulina ① indică linia galbenă.
                {
                    "url": self._form_url("purchase.purchase_rfq", self.po_preview),
                    "name": "06_preview_linie_galbena.png",
                    "wait": ".o_form_view",
                    **open_wizard,
                    "eval": "async () => {" + click_preview + widen + "}",
                    "highlight": [".modal tr.o_data_row:has-text('Teu PVC 110 x 50 mm')"],
                    "settle": 2500,
                },
                # Pasul 7: comanda din fluxul automat: nota colorată + activitatea de verificare.
                {
                    "url": self._form_url("purchase.purchase_rfq", self.po_activity),
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

        # Pasul 4: importul complet pe comanda confirmată (previzualizare → bifă pe
        # „Validează recepția din XML" → Importă) și jurnalul de rezultat.
        run_import = (
            "const sleep = ms => new Promise(r => setTimeout(r, ms));"
            "const click = async (sel) => { document.querySelector(sel).click(); await sleep(3500); };"
            "await click(\".modal-footer button[name='action_preview']\");"
            "document.querySelector(\".modal div[name='validate_receipt'] input\").click();"
            "await sleep(800);"
            "await click(\".modal-footer button[name='action_confirm_import']\");"
        )
        self.capture_screenshots(
            [
                {
                    "url": self._form_url("purchase.purchase_form_action", self.po_flow),
                    "name": "03_jurnal_rezultat.png",
                    "wait": ".o_form_view",
                    **open_wizard,
                    "eval": "async () => {" + run_import + widen + "}",
                    "highlight": [".modal-footer button[name='action_open_order']"],
                    "settle": 2500,
                },
            ],
            viewport=(1700, 1100),
        )
        self.env.invalidate_all()
        po = self.po_flow
        self.assertTrue(po.invoice_ids, "Importul din asistent trebuie să fi creat factura furnizorului")
        picking = po.picking_ids
        self.assertEqual(picking.state, "done", "Recepția trebuie să fie validată de import")
        bill = po.invoice_ids
        # În Odoo 20 evaluarea perpetuă se contabilizează „la facturare": validarea recepției
        # NU generează notă contabilă (verificat aici), nota apare la confirmarea facturii.
        stock_entries = picking.move_ids.account_move_id
        self.assertFalse(stock_entries, "Recepția nu trebuie să genereze notă contabilă proprie")

        shots = [
            # Pasul 5: comanda după import și recepția validată.
            {
                "url": self._form_url("purchase.purchase_form_action", po),
                "name": "04_comanda_importata.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='order_line'] .o_list_renderer"],
                "settle": 2500,
                "full": True,
            },
            {
                "url": self._form_url("stock.action_picking_tree_all", picking),
                "name": "05_receptie_validata.png",
                "wait": ".o_form_view",
                "settle": 2500,
                "full": True,
            },
            # Pasul 6: factura furnizorului, în ciornă, cu datele din XML.
            {
                "url": self._form_url("account.action_move_in_invoice_type", bill),
                "name": "08_factura_furnizor.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='ref']", "div[name='invoice_date']", "div[name='invoice_date_due']"],
                "settle": 2500,
                "full": True,
            },
        ]
        self.capture_screenshots(shots, viewport=(1700, 1100))

        # factura confirmată de operator (butonul standard **Confirmă**) → nota contabilă
        bill.action_post()
        self.env.flush_all()
        # Nota facturii: Dr 371 (stoc) + Dr 4426 (TVA deductibilă) = Cr 4011 (furnizori)
        balance = {}
        for line in bill.line_ids:
            code = line.account_id.code[:4]
            balance[code] = balance.get(code, 0.0) + line.balance
        self.assertEqual(sorted(balance), ["3710", "4011", "4426"], balance)
        self.capture_screenshots([self.account_move_shot(bill, "09_nota_factura.png")], viewport=(1700, 1100))
