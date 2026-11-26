# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Responsabilul transferurilor după grupul categoriei de produs" —
# generate în timpul testelor, în limba RO (fișa) și EN (readme/USAGE.md).
#
# Fluxul: grupul echipei cu membrii direcți, grupul care include echipa, categoria de produs
# cu grupul echipei, apoi livrările pregătite selectate și alocarea responsabililor.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_product_category_group,deltatech_doc_screenshots \
#       --test-tags=/deltatech_product_category_group:TestCategoryGroupScreenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# lista livrărilor: scoate filtrele implicite, afișează coloana opțională Responsabil și,
# la nevoie, bifează toate rândurile, ca să apară butonul Responsabil în bara de acțiuni
LIST_JS = """async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    for (const remove of document.querySelectorAll(".o_searchview_facet .o_facet_remove")) {
        remove.click();
        await sleep(600);
    }
    document.querySelector(".o_list_view .o_optional_columns_dropdown_toggle").click();
    await sleep(800);
    const input = [...document.querySelectorAll(".o-dropdown--menu input[type=checkbox]")].find((i) =>
        i.closest(".dropdown-item, label, span").textContent.trim() === "%(column)s"
    );
    if (input && !input.checked) {
        input.click();
    }
    // închide meniul coloanelor din același buton
    document.querySelector(".o_list_view .o_optional_columns_dropdown_toggle").click();
    await sleep(800);
    if (%(select)s) {
        const all = document.querySelector("thead .o_list_record_selector input");
        if (all && !all.checked) {
            all.click();
        }
        await sleep(800);
    }
    // bulina numerotată a evidențierii stă peste colțul celulei: celulele nu o mai taie
    document.querySelectorAll(".o_data_row td, .o_list_renderer").forEach((el) => (el.style.overflow = "visible"));
}"""

COLUMN = {"ro_RO": "Responsabil", "en_US": "Responsible"}


def _list_js(select):
    return {
        lang: LIST_JS % {"column": label, "select": "true" if select else "false"} for lang, label in COLUMN.items()
    }


@tagged("-at_install", "post_install", "fise_screenshots")
class TestCategoryGroupScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_product_category_group"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        env = cls.env
        group_stock_user = env.ref("stock.group_stock_user")
        admin = env.ref("base.user_admin")
        # drept de gestionar: butonul Responsabil e vizibil doar pentru Inventar / Administrator
        admin.write(
            {
                "group_ids": [
                    Command.link(env.ref("stock.group_stock_manager").id),
                ]
            }
        )
        cls.team = env["res.groups"].create({"name": "Echipa vopsele"})
        cls.leads = env["res.groups"].create({"name": "Șefi de tură", "implied_ids": [Command.link(cls.team.id)]})
        Users = env["res.users"].with_context(no_reset_password=True)
        company = env.company
        cls.ana, cls.mihai, cls.elena = Users.create(
            [
                {
                    "name": name,
                    "login": login,
                    "company_id": company.id,
                    "company_ids": [Command.set(company.ids)],
                    "group_ids": [Command.set([group.id, group_stock_user.id])],
                }
                for name, login, group in (
                    ("Ana Popescu", "ana.popescu", cls.team),
                    ("Mihai Ionescu", "mihai.ionescu", cls.team),
                    ("Elena Dumitru", "elena.dumitru", cls.leads),
                )
            ]
        )
        cls.category = env["product.category"].create({"name": "Vopsele", "user_group_id": cls.team.id})
        cls.product = env["product.product"].create(
            {
                "name": "Vopsea lavabilă albă 15 L",
                "default_code": "VOP-ALB15",
                "type": "consu",
                "is_storable": True,
                "categ_id": cls.category.id,
            }
        )
        cls.product.product_tmpl_id.update_field_translations(
            "name", {"ro_RO": "Vopsea lavabilă albă 15 L", "en_US": "White emulsion paint 15 L"}
        )
        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        stock = warehouse.lot_stock_id
        env["stock.quant"]._update_available_quantity(cls.product, stock, 100)
        customer = env["res.partner"].create({"name": "Client Demo SRL", "is_company": True})
        customers = env.ref("stock.stock_location_customers")
        # livrările existente ale bazei nu trebuie să apară în listă
        env["stock.picking"].search([("picking_type_id", "=", warehouse.out_type_id.id)]).action_cancel()
        Picking = env["stock.picking"]
        for index, qty in enumerate((5, 8, 3), start=1):
            picking = Picking.create(
                {
                    "picking_type_id": warehouse.out_type_id.id,
                    "partner_id": customer.id,
                    "origin": f"S0004{index}",
                    "location_id": stock.id,
                    "location_dest_id": customers.id,
                    "move_ids": [
                        Command.create(
                            {
                                "product_id": cls.product.id,
                                "product_uom_qty": qty,
                                "location_id": stock.id,
                                "location_dest_id": customers.id,
                            }
                        )
                    ],
                }
            )
            # numele fix: secvența livrărilor nu revine la rollback, iar capturile trebuie să fie stabile
            picking.name = f"WH/OUT/0000{index}"
            Picking |= picking
        cls.pickings = Picking
        cls.pickings.action_confirm()
        cls.pickings.action_assign()
        cls.pickings.user_id = False
        cls.out_action = env.ref("stock.action_picking_tree_outgoing").id

    def _list_url(self):
        return f"action={self.out_action}&view_type=list"

    def _shots_before(self):
        return [
            # 1. grupul echipei, membrii direcți
            {
                "url": f"id={self.team.id}&model=res.groups&view_type=form",
                "name": "01_grup_echipa_membri.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='user_ids']"],
            },
            # 2. grupul care include echipa
            {
                "url": f"id={self.leads.id}&model=res.groups&view_type=form",
                "name": "02_grup_sefi_include_echipa.png",
                "wait": ".o_form_view",
                "click_tab": {"ro_RO": "Moștenit", "en_US": "Inherited"},
                "highlight": ["div[name='implied_ids']"],
            },
            # 3. categoria de produs cu grupul echipei
            {
                "url": f"id={self.category.id}&model=product.category&view_type=form",
                "name": "03_categorie_grup_utilizatori.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='user_group_id']"],
            },
            # 4. livrările pregătite selectate și butonul Responsabil
            {
                "url": self._list_url(),
                "name": "04_transferuri_buton_responsabil.png",
                "wait": ".o_list_view .o_data_row",
                "eval": _list_js(select=True),
                "eval_wait": 1500,
                "highlight": ["button[name='responsible_determination']", ".o_data_row td[name='user_id']"],
            },
        ]

    def _shots_after(self):
        return [
            # 5. responsabilii alocați
            {
                "url": self._list_url(),
                "name": "05_responsabili_alocati.png",
                "wait": ".o_list_view .o_data_row",
                "eval": _list_js(select=False),
                "eval_wait": 1500,
                "highlight": [".o_data_row td[name='user_id']"],
            },
        ]

    def _capture(self, **kwargs):
        self.pickings.write({"user_id": False, "user_group_id": False})
        self.env.flush_all()
        self.capture_screenshots(self._shots_before(), viewport=(1600, 900), hide_systray=True, **kwargs)
        self.pickings.responsible_determination()
        self.assertEqual(self.pickings.user_id, self.ana | self.mihai | self.elena)
        self.env.flush_all()
        self.capture_screenshots(self._shots_after(), viewport=(1600, 900), hide_systray=True, **kwargs)

    def test_capture_fise(self):
        self._capture()

    def test_capture_usage(self):
        self._capture(lang="en_US")
