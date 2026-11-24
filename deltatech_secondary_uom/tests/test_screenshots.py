# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Cantități în unitatea secundară, cu factori de conversie
# pe produs" — generate în timpul testelor, pe compania „Demo UM Secundară SRL" în RON:
# în RO pentru fișă și în EN (static/description/en/) pentru readme/USAGE.md, plus GIF-ul
# demo pentru pagina de Apps Store.
#
# Seedează o gresie ținută în Unități (3 m² = 4 Unități, 15 kg = 1 Unități) și un profil
# ținut în m (1 Bară = 5,8 m), o comandă de vânzare confirmată în unitatea secundară (cu
# livrarea ei), o cerere de ofertă de achiziție în kg și o ofertă pentru GIF.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_secondary_uom,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import json
import unittest

from odoo import Command
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

SECONDARY_FIELDS = ("secondary_uom_qty", "secondary_uom_id")

# Coloanele „Cantitate secundară" și „Unitate secundară" sunt opționale și ascunse implicit:
# le afișăm din meniul de coloane al liniilor (bifele au `name` = câmpul, deci merg în orice limbă).
SHOW_SECONDARY_COLUMNS = """
    (async () => {
        const fields = __FIELDS__;
        const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
        const shown = (f) => document.querySelector(`.o_form_view .o_list_renderer th[data-name='${f}']`);
        const toggle = () => document.querySelector('.o_form_view .o_list_renderer .o_optional_columns_dropdown_toggle');
        for (let attempt = 0; attempt < 3 && fields.some((f) => !shown(f)); attempt++) {
            if (!document.querySelector('.o-dropdown--menu input[name]')) {
                toggle().click();
                await sleep(800);
            }
            for (const f of fields.filter((f) => !shown(f))) {
                const input = document.querySelector(`.o-dropdown--menu input[name='${f}']`);
                if (!input || input.checked) continue;
                // pe unele liste click-ul pe bifă comută de două ori (bifa + rândul meniului)
                (attempt & 1 ? input : input.closest('.o-dropdown-item') || input).click();
                await sleep(500);
            }
        }
        document.body.click();
        await sleep(600);
    })()
""".replace("__FIELDS__", json.dumps(SECONDARY_FIELDS))

# fereastra GIF-ului: destul de lată ca să încapă coloana Sumă de pe ofertă
GIF_VIEWPORT = (1360, 720)

PRODUCT_TAB = "a.nav-link[name='secondary_uom']"
OPEN_PRODUCT_TAB = f'document.querySelector("{PRODUCT_TAB}").click();'
LINE_COLUMNS = [f".o_form_view .o_list_renderer th[data-name='{f}']" for f in SECONDARY_FIELDS]


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSecondaryUomScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_secondary_uom"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo UM Secundară SRL")
        company = cls.env.company
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        # unitățile de măsură trebuie să fie vizibile pe comenzi și pe transferuri
        for xmlid in (
            "uom.group_uom",
            "purchase.group_purchase_manager",
            "sales_team.group_sale_manager",
            "stock.group_stock_manager",
        ):
            group = env.ref(xmlid)
            env.user.group_ids = [Command.link(group.id)]
            admin.group_ids = [Command.link(group.id)]
        env["res.config.settings"].create({"group_uom": True}).execute()
        env.flush_all()

        cls.uom_unit = env.ref("uom.product_uom_unit")
        cls.uom_m = env.ref("uom.product_uom_meter")
        cls.uom_m2 = env.ref("uom.product_uom_square_meter")
        cls.uom_kg = env.ref("uom.product_uom_kgm")
        cls.uom_bar = env["uom.uom"].create({"name": "Bară"})
        cls.uom_bar.update_field_translations("name", {"en_US": "Bar", "ro_RO": "Bară"})

        cls.customer = env["res.partner"].create({"name": "Construct Casa SRL", "country_id": env.ref("base.ro").id})
        cls.vendor = env["res.partner"].create({"name": "Ceramica Sud SRL", "country_id": env.ref("base.ro").id})

        # nume în română pentru depozit, operații și lista de prețuri (create înaintea limbii RO)
        cls.warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        cls.warehouse.write({"name": "Depozit central", "code": "WH"})
        cls.warehouse.in_type_id.name = "Recepții"
        cls.warehouse.out_type_id.name = "Livrări"
        env["product.pricelist"].search([]).write({"name": "Listă de prețuri RON"})

        cls.tile = env["product.template"].create(
            {
                "name": "Gresie porțelanată 75x100",
                "company_id": company.id,
                "is_storable": True,
                "uom_id": cls.uom_unit.id,
                "list_price": 89.0,
                "standard_price": 60.0,
                "secondary_uom_ids": [
                    # 3 m² = 4 plăci: o placă are 0,75 m²
                    Command.create({"uom_id": cls.uom_m2.id, "uom_qty": 3.0, "base_qty": 4.0}),
                    # 15 kg = 1 placă
                    Command.create({"uom_id": cls.uom_kg.id, "uom_qty": 15.0, "base_qty": 1.0}),
                ],
            }
        )
        cls.profile = env["product.template"].create(
            {
                "name": "Profil aluminiu 40x40",
                "company_id": company.id,
                "is_storable": True,
                "uom_id": cls.uom_m.id,
                "list_price": 42.0,
                "standard_price": 30.0,
                # 1 bară = 5,8 m
                "secondary_uom_ids": [Command.create({"uom_id": cls.uom_bar.id, "uom_qty": 1.0, "base_qty": 5.8})],
            }
        )

        # stoc inițial, ca livrarea să fie rezervată
        for product in (cls.tile, cls.profile):
            env["stock.quant"]._update_available_quantity(product.product_variant_id, cls.warehouse.lot_stock_id, 100.0)

        # comanda de vânzare introdusă în unitatea secundară, confirmată (cu livrarea ei)
        cls.sale = cls._order(
            "sale.order",
            cls.customer,
            [(cls.tile, cls.uom_m2, 40.0), (cls.profile, cls.uom_bar, 3.0)],
        )
        cls.sale.action_confirm()
        cls.delivery = cls.sale.picking_ids[:1]
        # cererea de ofertă de achiziție introdusă în kg
        cls.purchase = cls._order("purchase.order", cls.vendor, [(cls.tile, cls.uom_kg, 150.0)])
        # oferta pentru GIF: profilul pe 1 bară, schimbat apoi în GIF la 3 bare
        cls.quote = cls._order("sale.order", cls.customer, [(cls.profile, cls.uom_bar, 1.0)])

    @classmethod
    def _order(cls, model, partner, lines):
        """Comandă completată ca în interfață: unitatea secundară, apoi cantitatea secundară."""
        order_form = Form(cls.env[model])
        order_form.partner_id = partner
        for product, uom, qty in lines:
            with order_form.order_line.new() as line:
                line.product_id = product.product_variant_id
                line.secondary_uom_id = uom
                line.secondary_uom_qty = qty
        return order_form.save()

    def _product_shot(self, product, name):
        return {
            "url": f"id={product.id}&model=product.template&view_type=form",
            "name": name,
            "wait": ".o_form_view",
            "eval": OPEN_PRODUCT_TAB,
            "highlight": [PRODUCT_TAB, "div[name='secondary_uom_ids'] td[name='uom_id']"],
            "settle": 2000,
        }

    def _line_shot(self, record, name, highlight=None):
        return {
            "url": f"id={record.id}&model={record._name}&view_type=form",
            "name": name,
            "wait": ".o_form_view",
            "eval": SHOW_SECONDARY_COLUMNS,
            "eval_wait": 2800,
            "highlight": highlight or LINE_COLUMNS,
            "settle": 2000,
        }

    def _shots(self):
        return [
            # 1. gresia: 3 m² = 4 Unități și 15 kg = 1 Unități
            self._product_shot(self.tile, "01_produs_gresie_unitati_alternative.png"),
            # 2. profilul: 1 Bară = 5,8 m
            self._product_shot(self.profile, "02_produs_profil_bara.png"),
            # 3. comanda de vânzare în unitatea secundară
            self._line_shot(
                self.sale,
                "03_comanda_vanzare_unitate_secundara.png",
                LINE_COLUMNS + [".o_form_view .o_list_renderer th[data-name='product_uom_qty']"],
            ),
            # 4. livrarea preia unitatea secundară
            self._line_shot(self.delivery, "04_livrare_unitate_secundara.png"),
            # 5. comanda de achiziție în kg
            self._line_shot(
                self.purchase,
                "05_comanda_achizitie_unitate_secundara.png",
                LINE_COLUMNS + [".o_form_view .o_list_renderer th[data-name='product_qty']"],
            ),
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), hide_systray=True, lang="en_US")

    def _gif_steps(self):
        menu = self.env.ref("sale.sale_menu_root")
        qty_cell = ".o_form_view .o_list_renderer .o_data_row:first-child td[name='secondary_uom_qty']"
        return [
            {
                "goto": f"id={self.quote.id}&model=sale.order&view_type=form&menu_id={menu.id}",
                "wait": ".o_form_view",
            },
            {"eval": SHOW_SECONDARY_COLUMNS, "hold": 600},
            {
                "caption": {
                    "ro_RO": "Profilul se ține în stoc în metri",
                    "en_US": "The profile is stocked in metres",
                },
                "move": ".o_form_view .o_list_renderer .o_data_row:first-child td[name='product_uom_qty']",
                "hold": 1800,
            },
            {
                "caption": {
                    "ro_RO": "Clientul îl comandă însă la bară",
                    "en_US": "The customer orders it by the bar",
                },
                "move": ".o_form_view .o_list_renderer .o_data_row:first-child td[name='secondary_uom_id']",
                "hold": 1800,
            },
            {
                "caption": {
                    "ro_RO": "Agentul scrie direct 3 bare",
                    "en_US": "The salesperson simply types 3 bars",
                },
                "click": qty_cell,
                "hold": 400,
            },
            {"type": "3", "into": f"{qty_cell} input", "clear": True, "hold": 500},
            {"press": "Tab", "hold": 400},
            {
                "caption": {
                    "ro_RO": "La salvare, metrii se calculează singuri",
                    "en_US": "On save, the metres are computed",
                },
                "click": ".o_form_button_save",
                "hold": 1500,
            },
            {
                "caption": {
                    "ro_RO": "3 bare de 5,8 m înseamnă 17,40 m",
                    "en_US": "3 bars of 5.8 m make 17.40 m",
                },
                "move": ".o_form_view .o_list_renderer .o_data_row:first-child td[name='product_uom_qty']",
                "hold": 2500,
            },
            {
                "caption": {
                    "ro_RO": "Prețul și stocul rămân pe metru",
                    "en_US": "Price and stock stay per metre",
                },
                "move": ".o_form_view .o_list_renderer .o_data_row:first-child td[name='price_subtotal']",
                "hold": 2500,
            },
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_gif(self):
        self.capture_gif(self._gif_steps(), viewport=GIF_VIEWPORT, lang="en_US")
