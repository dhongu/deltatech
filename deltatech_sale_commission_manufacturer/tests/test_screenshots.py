# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Producătorul în raportul de analiză a profitului" — generate în
# timpul testelor, în limba RO, pe compania „Demo Distribuție SRL" în RON.
#
# Seed: cel din fișa Sale Commission (trei facturi din luna trecută, livrate, cu costul din
# livrare), plus doi producători pe produse:
#   - Nord Computers SRL: Laptop 14" (vânzare 35.000, cost 28.000) și Monitor 27" (7.000 / 5.000)
#     → vânzare 42.000, cost 33.000, profit 9.000;
#   - Periferice Tech SRL: Mouse wireless (1.800 / 1.000) → profit 800.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i l10n_ro,l10n_ro_doc_screenshots,deltatech_sale_commission_manufacturer \
#       --test-tags=fise_screenshots/deltatech_sale_commission_manufacturer --stop-after-init
from odoo import Command
from odoo.tests import tagged

# importăm modulul, nu clasa: o clasă de test importată în spațiul de nume ar rula și aici
from odoo.addons.deltatech_sale_commission.tests import test_screenshots as commission_screenshots

# Tastează în căutare, ca să apară propunerile câmpurilor (inclusiv „Producător").
JS_TYPE_SEARCH = """
() => {
    const input = document.querySelector('.o_searchview_input');
    input.focus();
    input.value = 'Nord';
    input.dispatchEvent(new Event('input', {bubbles: true}));
}
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSaleMarginManufacturerScreenshots(commission_screenshots.TestSaleCommissionScreenshots):
    screenshots_module = "deltatech_sale_commission_manufacturer"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env

        def manufacturer(name):
            return env["res.partner"].create({"name": name, "is_company": True, "is_manufacturer": True})

        nord = manufacturer("Nord Computers SRL")
        (cls.laptop | cls.monitor).product_tmpl_id.manufacturer_id = nord
        cls.mouse.product_tmpl_id.manufacturer_id = manufacturer("Periferice Tech SRL")
        # același raport, deschis direct pe pivotul grupat după producător (ca după alegerea
        # „Grupează după > Producător" din căutare)
        cls.act_margin_manufacturer = cls.act_margin.copy(
            {
                "path": False,
                # copy() nu copiază view_ids: fără pivotul cu secvența 1, lista ar fi prima
                "view_ids": [
                    Command.create(
                        {
                            "sequence": 1,
                            "view_mode": "pivot",
                            "view_id": env.ref("deltatech_sale_margin.view_sale_margin_report_pivot").id,
                        }
                    )
                ],
                "context": "{'search_default_filter_date': 1, 'search_default_group_manufacturer': 1}",
            }
        )

    def test_capture_fise(self):
        self.env.flush_all()
        self.capture_screenshots(
            [
                {
                    "url": f"action={self.act_margin.id}&view_type=pivot",
                    "name": "01_raport_profit_cautare_producator.png",
                    "wait": ".o_pivot",
                    "settle": 2000,
                    "eval": JS_TYPE_SEARCH,
                    "eval_wait": 1500,
                    "highlight": [".o_searchview_autocomplete .dropdown-item:has-text('Producător')"],
                },
                {
                    "url": f"action={self.act_margin_manufacturer.id}&view_type=pivot",
                    "name": "02_raport_profit_grupare_producator.png",
                    "wait": ".o_pivot",
                    "settle": 3000,
                },
            ],
            hide_systray=True,
        )
