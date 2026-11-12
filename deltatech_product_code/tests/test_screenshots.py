# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Codificarea automată a produselor" — generate în timpul
# testelor, în limba RO, pe compania „RO Company" în RON.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_product_code,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


# formularul unui produs nou: numele și categoria completate ca de operator
FILL_NEW_PRODUCT = """async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    for (let t = 0; t < 15000 && !document.querySelector("div[name='name'] :is(input, textarea)"); t += 200) {
        await sleep(200);
    }
    await sleep(800);
    const name = document.querySelector("div[name='name'] :is(input, textarea)");
    name.focus();
    name.value = 'Filtru de ulei';
    name.dispatchEvent(new Event('input', {bubbles: true}));
    name.dispatchEvent(new Event('change', {bubbles: true}));
    const categ = document.querySelector("div[name='categ_id'] input");
    categ.focus();
    categ.value = 'Piese de schimb';
    categ.dispatchEvent(new Event('input', {bubbles: true}));
    for (let t = 0; t < 10000 && !document.querySelector('.o-autocomplete--dropdown-item'); t += 200) {
        await sleep(200);
    }
    const item = document.querySelector('.o-autocomplete--dropdown-item a, .o-autocomplete--dropdown-item');
    if (item) { item.click(); }
    await sleep(800);
}"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestProductCodeScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_product_code"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        env = cls.env
        # planul de conturi și taxele RO, ca pe ecrane să apară conturile OMFP și TVA 21%
        if env.company.chart_template != "ro":
            env["account.chart.template"].try_loading("ro", company=env.company, install_demo=False)
        sequence = env["ir.sequence"].create(
            {"name": "Coduri produse", "code": "product.code.shots", "prefix": "ZZ", "padding": 4}
        )
        cls.category = env["product.category"].create(
            {
                "name": "Piese de schimb",
                "sequence_id": sequence.id,
                "generate_barcode": True,
                "barcode_source": "internal",
                "prefix_barcode": "20",
                "barcode_random": False,
            }
        )
        # produsul de la pașii 3 și 4: codurile generate la creare
        cls.coded_product = env["product.template"].create({"name": "Filtru de aer", "categ_id": cls.category.id})
        cls.product_action = env.ref("product.product_template_action")
        env.flush_all()
        env.invalidate_all()

    def _shots(self):
        product_form = "model=product.template&view_type=form&id="
        return [
            # 1. Categoria cu secvența și opțiunile de cod de bare
            {
                "url": f"id={self.category.id}&model=product.category&view_type=form",
                "name": "01_categorie.png",
                "wait": ".o_form_view",
                "settle": 2000,
                "highlight": ["div[name='sequence_id']", "div[name='generate_barcode']", "div[name='barcode_source']"],
            },
            # 2. Produs nou, nesalvat: categoria aleasă, referința și codul de bare goale
            {
                "url": "model=product.template&view_type=form&action=" + str(self.product_action.id),
                "eval": FILL_NEW_PRODUCT,
                "name": "02_produs_nou.png",
                "wait": ".o_form_view",
                "eval_wait": 1500,
                "settle": 2500,
                "highlight": ["div[name='categ_id']", "div[name='default_code']", "div[name='barcode']"],
            },
            # 3. Produs salvat: codurile generate
            {
                "url": product_form + str(self.coded_product.id),
                "name": "03_cod_generat.png",
                "wait": ".o_form_view",
                "settle": 2500,
                "highlight": ["div[name='default_code']", "div[name='barcode']"],
            },
            # 4. Meniul Acțiuni
            {
                "url": product_form + str(self.coded_product.id),
                "name": "04_actiuni_produs.png",
                "wait": ".o_form_view",
                "click_btn": ".o_cp_action_menus button",
                "settle": 2500,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")
