# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Unitățile de măsură pe achiziții" — generate în timpul
# testelor, pe compania „Demo UM SRL" în RON: în RO pentru fișă și în EN
# (static/description/en/) pentru readme/USAGE.md.
#
# Seedează o grindă ținută în stoc la bucată și cumpărată la m³ (unitatea implicită
# de achiziție m³, fără linie de furnizor) și un șurub în Unități, fără ambalaje pe
# produs, cu o unitate „Cutie 100 buc" din același arbore și o linie de furnizor.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_uom_domain,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=/deltatech_uom_domain:TestUomDomainScreenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# Tab-ul „Achiziție" din formularul produsului.
OPEN_PURCHASE_TAB = """
    [...document.querySelectorAll('.o_notebook .nav-link')]
        .find((a) => a.textContent.includes('%(label)s')).click();
"""

# Deschide lista de unități de pe prima linie a unei liste editabile (comandă sau furnizori).
OPEN_UOM_DROPDOWN = """
    new Promise((resolve) => {
        %(before)s
        setTimeout(() => {
            document.querySelector('.o_field_one2many tr.o_data_row td[name="uom_id"]').click();
            setTimeout(() => {
                const input = document.querySelector('.o_field_one2many tr.o_data_row td[name="uom_id"] input');
                input.focus();
                input.click();
                setTimeout(resolve, 1500);
            }, 1000);
        }, 800);
    })
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestUomDomainScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_uom_domain"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo UM SRL")
        company = cls.env.company
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        # unitățile de măsură trebuie să fie vizibile în formulare și pe comenzi
        for xmlid in ("uom.group_uom", "purchase.group_purchase_manager"):
            group = env.ref(xmlid)
            env.user.group_ids = [Command.link(group.id)]
            admin.group_ids = [Command.link(group.id)]
        env["res.config.settings"].create({"group_uom": True}).execute()
        env.flush_all()

        uom_unit = env.ref("uom.product_uom_unit")
        uom_m3 = env.ref("uom.product_uom_cubic_meter")
        cls.vendor = env["res.partner"].create({"name": "Gater Bistrița SRL", "country_id": env.ref("base.ro").id})
        cls.vendor_screws = env["res.partner"].create(
            {"name": "Feronerie Nord SRL", "country_id": env.ref("base.ro").id}
        )
        # nume în română pentru depozit și recepții (create înaintea limbii RO)
        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        warehouse.write({"name": "Depozit central", "code": "WH"})
        warehouse.in_type_id.name = "Recepții"
        env["product.pricelist"].search([]).write({"name": "Listă de prețuri RON"})

        # unități din arborii m³ și Unități, nelegate de niciun produs
        uom_beam = env["uom.uom"].create(
            {"name": "buc grindă (0,0384 m³)", "relative_uom_id": uom_m3.id, "relative_factor": 0.0384}
        )
        env["uom.uom"].create({"name": "Cutie 100 buc", "relative_uom_id": uom_unit.id, "relative_factor": 100})

        # grinda: în stoc la bucată, cumpărată la m³, fără linie de furnizor
        cls.beam = env["product.template"].create(
            {
                "name": "Grindă molid 8x8 cm, 6 m",
                "is_storable": True,
                "uom_id": uom_beam.id,
                "purchase_uom_id": uom_m3.id,
                "standard_price": 48.0,
            }
        )
        # șurubul: în Unități, fără ambalaje pe produs, cu o linie de furnizor
        cls.screw = env["product.template"].create(
            {
                "name": "Șurub autoforant 4,2x13",
                "is_storable": True,
                "uom_id": uom_unit.id,
                "standard_price": 0.15,
                "seller_ids": [Command.create({"partner_id": cls.vendor_screws.id, "price": 0.15})],
            }
        )

        cls.rfq_beam = cls._rfq(cls.vendor, cls.beam, 4.5)
        cls.rfq_screw = cls._rfq(cls.vendor_screws, cls.screw, 500)

    @classmethod
    def _rfq(cls, vendor, product, qty):
        po_form = Form(cls.env["purchase.order"])
        po_form.partner_id = vendor
        with po_form.order_line.new() as line:
            line.product_id = product.product_variant_id
            line.product_qty = qty
        return po_form.save()

    def _shots(self):
        purchase_tab = {
            "ro_RO": OPEN_PURCHASE_TAB % {"label": "Achizi"},
            "en_US": OPEN_PURCHASE_TAB % {"label": "Purchase"},
        }
        return [
            # 1. produsul: unitatea implicită de achiziție m³, în tab-ul Achiziție
            {
                "url": f"id={self.beam.id}&model=product.template&view_type=form",
                "name": "01_produs_um_implicita_achizitie.png",
                "wait": ".o_form_view",
                "eval": purchase_tab,
                "highlight": ["div[name='purchase_uom_id']"],
                "settle": 2000,
            },
            # 2. cererea de ofertă fără linie de furnizor: linia ia m³
            {
                "url": f"id={self.rfq_beam.id}&model=purchase.order&view_type=form",
                "name": "02_cerere_oferta_um_implicita.png",
                "wait": ".o_form_view",
                "highlight": [".o_field_one2many td[name='uom_id']"],
                "settle": 2000,
            },
            # 3. cererea de ofertă a șurubului: lista de unități din arborele Unități
            {
                "url": f"id={self.rfq_screw.id}&model=purchase.order&view_type=form",
                "name": "03_cerere_oferta_lista_um.png",
                "wait": ".o_form_view",
                "eval": OPEN_UOM_DROPDOWN % {"before": ""},
                "eval_wait": 4000,
                "highlight": [".o-autocomplete--dropdown-menu"],
                "settle": 1500,
            },
            # 4. linia de furnizor a șurubului: tot doar unitățile din arborele Unități
            {
                "url": f"id={self.screw.id}&model=product.template&view_type=form",
                "name": "04_furnizor_lista_um.png",
                "wait": ".o_form_view",
                "eval": {lang: OPEN_UOM_DROPDOWN % {"before": script} for lang, script in purchase_tab.items()},
                "eval_wait": 4000,
                "highlight": [".o-autocomplete--dropdown-menu"],
                "settle": 1500,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), hide_systray=True, lang="en_US")
