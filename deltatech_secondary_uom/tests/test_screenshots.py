# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Unități alternative cu factor de conversie pe produs” — generate
# în timpul testelor, pe compania „Demo UM SRL” în RON: în RO pentru fișă și în EN
# (static/description/en/) pentru readme/USAGE.md, plus GIF-ul demo pentru Apps Store.
#
# Seedează unitatea „Bară” și două produse în metri: profilul de aluminiu (1 Bară = 6 m) și țeava
# de inox (1 Bară = 5 m), o comandă de vânzare de 10 bare și o comandă de achiziție confirmată
# de 8 bare, cu recepția ei.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_secondary_uom,l10n_ro,deltatech_doc_screenshots \
#       --test-tags=/deltatech_secondary_uom:TestSecondaryUomScreenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# Afișează coloanele opționale „Cantitate secundară” și „Unitate secundară” din lista de linii.
SHOW_SECONDARY_COLUMNS = """
    new Promise((resolve) => {
        const wait = (ms) => new Promise((r) => setTimeout(r, ms));
        (async () => {
            try {
                %(before)s
                await wait(1000);
                const toggle = () => document.querySelector(
                    ".o_field_widget[name='%(field)s'] .o_optional_columns_dropdown_toggle"
                );
                if (!toggle()) {
                    return;
                }
                toggle().click();
                await wait(800);
                for (const name of ["secondary_uom_qty", "secondary_uom_id"]) {
                    const input = document.querySelector(`.o_optional_columns_dropdown input[name='${name}']`);
                    if (input && !input.checked) {
                        input.click();
                        await wait(500);
                    }
                }
                if (toggle()) {
                    toggle().click();
                }
                await wait(800);
            } finally {
                resolve();
            }
        })();
    })
"""

# Tab-ul operațiunilor din recepție.
OPEN_OPERATIONS_TAB = """
    const tab = document.querySelector(".o_notebook .nav-link[name='operations']");
    if (tab) { tab.click(); }
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSecondaryUomScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_secondary_uom"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo UM SRL")
        company = cls.env.company
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        for xmlid in (
            "uom.group_uom",
            "sales_team.group_sale_manager",
            "purchase.group_purchase_manager",
            "stock.group_stock_manager",
        ):
            group = env.ref(xmlid)
            env.user.group_ids = [Command.link(group.id)]
            admin.group_ids = [Command.link(group.id)]
        env["res.config.settings"].create({"group_uom": True}).execute()
        env.flush_all()

        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        warehouse.write({"name": "Depozit central", "code": "WH"})
        warehouse.in_type_id.name = "Recepții"
        warehouse.out_type_id.name = "Livrări"
        env["product.pricelist"].search([]).write({"name": "Listă de prețuri RON"})

        uom_m = env.ref("uom.product_uom_meter")
        cls.uom_bar = env["uom.uom"].create({"name": "Bară"})
        ro = env.ref("base.ro").id
        cls.customer = env["res.partner"].create({"name": "Construct Vest SRL", "country_id": ro})
        cls.vendor = env["res.partner"].create({"name": "Metal Profil SRL", "country_id": ro})

        cls.profile = env["product.template"].create(
            {
                "name": "Profil aluminiu 40x40",
                "is_storable": True,
                "uom_id": uom_m.id,
                "list_price": 32.0,
                "standard_price": 18.0,
                "secondary_uom_ids": [
                    Command.create({"uom_id": cls.uom_bar.id, "uom_qty": 1.0, "base_qty": 6.0}),
                ],
            }
        )
        cls.pipe = env["product.template"].create(
            {
                "name": "Țeavă inox 25 mm",
                "is_storable": True,
                "uom_id": uom_m.id,
                "list_price": 35.0,
                "standard_price": 20.0,
                "secondary_uom_ids": [
                    Command.create({"uom_id": cls.uom_bar.id, "uom_qty": 1.0, "base_qty": 5.0}),
                ],
            }
        )

        # ca interfața: linia primește și cantitatea calculată (60 m), nu doar cantitatea în bare
        # (vezi issue #4246, subtotalul rămâne pe cantitatea 1 fără ea)
        cls.sale_order = env["sale.order"].create(
            {
                "partner_id": cls.customer.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.profile.product_variant_id.id,
                            "product_uom_qty": 60.0,
                            "secondary_uom_id": cls.uom_bar.id,
                            "secondary_uom_qty": 10.0,
                        }
                    )
                ],
            }
        )

        po_form = Form(env["purchase.order"])
        po_form.partner_id = cls.vendor
        with po_form.order_line.new() as line:
            line.product_id = cls.pipe.product_variant_id
            line.secondary_uom_id = cls.uom_bar
            line.secondary_uom_qty = 8.0
            line.price_unit = 20.0
        cls.purchase_order = po_form.save()
        cls.purchase_order.button_confirm()
        cls.receipt = cls.purchase_order.picking_ids[:1]

    def _shots(self):
        return [
            # 1. profilul: 1 Bară = 6 m
            {
                "url": f"id={self.profile.id}&model=product.template&view_type=form",
                "name": "01_produs_unitati_alternative.png",
                "wait": ".o_form_view",
                "click_tab": {"ro_RO": "Unități alternative", "en_US": "Alternative Units"},
                "highlight": ["div[name='secondary_uom_ids'] tr.o_data_row"],
                "settle": 2000,
            },
            # 2. țeava: aceeași unitate, 1 Bară = 5 m
            {
                "url": f"id={self.pipe.id}&model=product.template&view_type=form",
                "name": "02_produs_b_unitati_alternative.png",
                "wait": ".o_form_view",
                "click_tab": {"ro_RO": "Unități alternative", "en_US": "Alternative Units"},
                "highlight": ["div[name='secondary_uom_ids'] tr.o_data_row"],
                "settle": 2000,
            },
            # 3. comanda de vânzare: 10 bare = 60 m
            {
                "url": f"id={self.sale_order.id}&model=sale.order&view_type=form",
                "name": "03_comanda_vanzare_bare.png",
                "wait": ".o_form_view",
                "eval": SHOW_SECONDARY_COLUMNS % {"before": "", "field": "order_line"},
                "highlight": [
                    ".o_field_widget td[name='secondary_uom_qty']",
                    ".o_field_widget tr.o_data_row td:has(div[name='product_uom_qty'])",
                ],
                "settle": 2000,
            },
            # 4. comanda de achiziție: 8 bare = 40 m, preț pe metru
            {
                "url": f"id={self.purchase_order.id}&model=purchase.order&view_type=form",
                "name": "04_comanda_achizitie_bare.png",
                "wait": ".o_form_view",
                "eval": SHOW_SECONDARY_COLUMNS % {"before": "", "field": "order_line"},
                "highlight": [
                    ".o_field_widget td[name='secondary_uom_qty']",
                    ".o_field_widget td[name='product_qty']",
                    ".o_field_widget td[name='price_unit']",
                ],
                "settle": 2000,
            },
            # 5. recepția: mișcarea păstrează bara
            {
                "url": f"id={self.receipt.id}&model=stock.picking&view_type=form",
                "name": "05_receptie_bare.png",
                "wait": ".o_form_view",
                "eval": SHOW_SECONDARY_COLUMNS % {"before": OPEN_OPERATIONS_TAB, "field": "move_ids"},
                "highlight": [".o_field_widget td[name='secondary_uom_qty']"],
                "settle": 2000,
            },
        ]

    def _gif_steps(self):
        product_url = f"id={self.profile.id}&model=product.template&view_type=form"
        so_url = f"id={self.sale_order.id}&model=sale.order&view_type=form"
        receipt_url = f"id={self.receipt.id}&model=stock.picking&view_type=form"
        tab = {
            "ro_RO": ".o_notebook .nav-link:has-text('Unități alternative')",
            "en_US": ".o_notebook .nav-link:has-text('Alternative Units')",
        }
        return [
            {"goto": product_url, "wait": ".o_form_view"},
            {
                "caption": {
                    "ro_RO": "Fiecare produs își are propria bară",
                    "en_US": "Each product has its own bar length",
                },
                "click": tab,
                "hold": 2500,
            },
            {
                "caption": {"ro_RO": "Aici, o bară înseamnă 6 metri", "en_US": "Here, one bar means 6 metres"},
                "move": "div[name='secondary_uom_ids']",
                "hold": 2500,
            },
            {
                "goto": so_url,
                "wait": ".o_form_view",
                "eval": SHOW_SECONDARY_COLUMNS % {"before": "", "field": "order_line"},
            },
            {
                "caption": {
                    "ro_RO": "Pe comandă se scriu 10 bare, linia are 60 m",
                    "en_US": "The order takes 10 bars, the line gets 60 m",
                },
                "move": ".o_field_widget td[name='secondary_uom_qty']",
                "hold": 3000,
            },
            {
                "goto": receipt_url,
                "wait": ".o_form_view",
                "eval": SHOW_SECONDARY_COLUMNS % {"before": "", "field": "move_ids"},
            },
            {
                "caption": {
                    "ro_RO": "Recepția păstrează cantitatea în bare",
                    "en_US": "The receipt keeps the quantity in bars",
                },
                "move": ".o_field_widget td[name='secondary_uom_qty']",
                "hold": 3000,
            },
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), hide_systray=True, lang="en_US")

    def test_capture_gif(self):
        # suita deltatech are doar pagina EN pe Apps Store: GIF-ul RO nu se folosește
        self.capture_gif(self._gif_steps(), lang="en_US")
