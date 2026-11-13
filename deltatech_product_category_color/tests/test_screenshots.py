# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Culori pe categoriile de produse" — generate în timpul
# testelor, în limba RO (fișa), pe compania „Demo Depozit SRL" în RON (numele „RO Company" există deja în baza dedicată).
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i l10n_ro,deltatech_product_category_color,deltatech_doc_screenshots \
#       --test-tags=/deltatech_product_category_color:TestCategoryColorScreenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# indexuri din paleta de culori Odoo
COLOR_RED = 1
COLOR_BLUE = 8
COLOR_GREEN = 10
SEARCH_JS = (
    "(async () => {"
    "const input = document.querySelector('.o_searchview_input');"
    "input.focus(); input.value = 'DC/';"
    "input.dispatchEvent(new Event('input', {bubbles: true}));"
    "await new Promise(r => setTimeout(r, 300));"
    "input.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));"
    "})()"
)


@tagged("-at_install", "post_install", "fise_screenshots")
class TestCategoryColorScreenshots(ScreenshotCase or TransactionCase):
    screenshots_module = "deltatech_product_category_color"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Depozit SRL")
        env = cls.env
        company = env.company
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        admin.group_ids = [Command.link(env.ref("stock.group_stock_manager").id)]

        Category = env["product.category"]
        cls.cat_frozen = Category.create({"name": "Alimente congelate", "color": COLOR_BLUE})
        cls.cat_detergent = Category.create({"name": "Detergenți", "color": COLOR_RED})
        cls.cat_pack = Category.create({"name": "Ambalaje", "color": COLOR_GREEN})

        Product = env["product.product"]
        peas = Product.create({"name": "Mazăre congelată 1 kg", "categ_id": cls.cat_frozen.id, "is_storable": True})
        soap = Product.create({"name": "Detergent lichid 5 l", "categ_id": cls.cat_detergent.id, "is_storable": True})
        box = Product.create({"name": "Cutie carton 40×30", "categ_id": cls.cat_pack.id, "is_storable": True})

        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        cls.type_in = warehouse.in_type_id
        cls.type_out = warehouse.out_type_id
        cls.type_in.update_field_translations("name", {"ro_RO": "Recepții", "en_US": "Receipts"})
        cls.type_out.update_field_translations("name", {"ro_RO": "Livrări", "en_US": "Delivery Orders"})
        if "auto_batch" in cls.type_in._fields:
            (cls.type_in | cls.type_out).auto_batch = False

        ro = env.ref("base.ro").id
        Partner = env["res.partner"]
        vendor = Partner.create({"name": "Frig Distribuție SRL", "country_id": ro, "city": "Pitești"})
        customer = Partner.create({"name": "Casa Verde SRL", "country_id": ro, "city": "Sibiu"})

        def make_picking(ptype, partner, products, name):
            picking = env["stock.picking"].create(
                {
                    "partner_id": partner.id,
                    "picking_type_id": ptype.id,
                    "move_ids": [
                        Command.create(
                            {
                                "product_id": product.id,
                                "product_uom_qty": qty,
                                "uom_id": product.uom_id.id,
                                "location_id": ptype.default_location_src_id.id,
                                "location_dest_id": ptype.default_location_dest_id.id,
                            }
                        )
                        for product, qty in products
                    ],
                }
            )
            picking.name = name
            picking.action_confirm()
            return picking

        make_picking(cls.type_in, vendor, [(peas, 40.0), (box, 100.0)], "DC/IN/00021")
        env["stock.quant"]._update_available_quantity(soap, warehouse.lot_stock_id, 30.0)
        delivery = make_picking(cls.type_out, customer, [(soap, 6.0)], "DC/OUT/00045")
        delivery.action_assign()
        # livrare nerezervată: nu există stoc de mazăre
        make_picking(cls.type_out, customer, [(peas, 10.0)], "DC/OUT/00046")
        env.flush_all()

    def _shots(self):
        action = self.env.ref("stock.action_picking_tree_all").id
        return [
            # 1. formularul categoriei, cu câmpul „Index culoare"
            {
                "url": f"id={self.cat_frozen.id}&model=product.category&view_type=form",
                "name": "01_categorie_culoare.png",
                "wait": ".o_form_view",
                "settle": 2000,
                # paleta de culori se deschide din butonul „Index culoare"
                "click_btn": "div[name='color'] .o_colorlist_toggler",
                "wait_after": ".o_colorlist",
                "highlight": [".o_colorlist"],
            },
            # 2. transferurile în Kanban, cu etichetele colorate ale categoriilor
            {
                "url": f"action={action}&view_type=kanban",
                "name": "02_transferuri_kanban.png",
                "wait": ".o_kanban_view .o_kanban_record",
                # în baza dedicată există și transferuri demo: filtrăm după prefixul DC/
                "eval": SEARCH_JS,
                "eval_wait": 2500,
                "settle": 1000,
                "highlight": [".o_kanban_record:has-text('DC/IN/00021') .o_field_many2many_tags"],
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())
