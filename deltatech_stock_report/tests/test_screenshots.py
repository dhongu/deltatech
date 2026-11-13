# Copyright (C) 2026 Terrabit
# License OPL-1 (https://www.odoo.com/documentation/user/legal/licenses/licenses.html)
#
# Capturi de ecran pentru fișa consultant „Analiza pozițiilor din transferuri".
#
# Seedează recepții de la doi furnizori și livrări către doi clienți (unul prin persoană de
# contact), produse din două categorii, toate validate.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_stock_report,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestStockReportScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_stock_report"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_demo_company()
        env = cls.env = cls.env["base"].with_company(company).env
        cls.warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        if not cls.warehouse:
            cls.warehouse = env["stock.warehouse"].create(
                {"name": "Depozit principal", "code": "DP", "company_id": company.id}
            )
        stock = cls.warehouse.lot_stock_id
        suppliers = env.ref("stock.stock_location_suppliers")
        customers = env.ref("stock.stock_location_customers")

        categ_a = env["product.category"].create({"name": "Materii prime"})
        categ_b = env["product.category"].create({"name": "Produse finite"})

        def product(name, categ, cost):
            return env["product.product"].create(
                {
                    "name": name,
                    "type": "consu",
                    "is_storable": True,
                    "categ_id": categ.id,
                    "standard_price": cost,
                }
            )

        p1 = product("Foi de tablă 2 mm", categ_a, 45.0)
        p2 = product("Șuruburi M8 (cutie)", categ_a, 12.5)
        p3 = product("Raft metalic", categ_b, 210.0)

        def partner(name, **kw):
            return env["res.partner"].create({"name": name, **kw})

        furn1 = partner("Metal Trade SRL", is_company=True)
        furn2 = partner("Fixing Supply SRL", is_company=True)
        cli1 = partner("Depozite Nord SRL", is_company=True)
        cli2 = partner("Magazin Sud SRL", is_company=True)
        contact = partner("Ioana Marinescu", parent_id=cli2.id, type="contact")

        def validate(ptype, src, dst, partner_rec, lines):
            picking = env["stock.picking"].create(
                {
                    "picking_type_id": ptype.id,
                    "location_id": src.id,
                    "location_dest_id": dst.id,
                    "partner_id": partner_rec.id,
                    "move_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": prod.id,
                                "product_uom_qty": qty,
                                "location_id": src.id,
                                "location_dest_id": dst.id,
                            },
                        )
                        for prod, qty in lines
                    ],
                }
            )
            picking.action_confirm()
            for move in picking.move_ids:
                move.quantity = move.product_uom_qty
                move.picked = True
            picking.with_context(skip_backorder=True, skip_sms=True).button_validate()
            return picking

        validate(cls.warehouse.in_type_id, suppliers, stock, furn1, [(p1, 100), (p2, 400)])
        validate(cls.warehouse.in_type_id, suppliers, stock, furn2, [(p2, 200), (p3, 30)])
        validate(cls.warehouse.out_type_id, stock, customers, cli1, [(p3, 12), (p1, 20)])
        validate(cls.warehouse.out_type_id, stock, customers, contact, [(p3, 8), (p2, 150)])
        env.flush_all()
        cls.action_id = env.ref("deltatech_stock_report.action_stock_picking_report").id

    def _shots(self):
        act = self.action_id
        # deschide panoul de filtre/grupări al barei de căutare
        open_search = (
            "document.querySelector('.o_searchview_dropdown_toggler').click();new Promise(r => setTimeout(r, 1200));"
        )
        pivot = f"action={act}&view_type=pivot"
        select_all = (
            "(async () => {"
            "document.querySelector('.o_list_view thead .o_list_record_selector input').click();"
            "await new Promise(r => setTimeout(r, 800));"
            "document.querySelector('.o_cp_action_menus .dropdown-toggle').click();"
            "await new Promise(r => setTimeout(r, 1000));"
            "})()"
        )
        return [
            {
                "url": pivot,
                "name": "01_meniu_raport.png",
                "wait": ".o_pivot",
                "click_btn": {
                    "ro_RO": ".o_main_navbar :is(button,a):has-text('Raportare')",
                    "en_US": ".o_main_navbar :is(button,a):has-text('Reporting')",
                },
                "wait_after": ".o-dropdown--menu",
                "highlight": {
                    "ro_RO": ".o-dropdown--menu .dropdown-item:has-text('Analiză transferuri')",
                    "en_US": ".o-dropdown--menu .dropdown-item:has-text('Picking Analysis')",
                },
                "settle": 1500,
            },
            {
                "url": pivot,
                "name": "02_pivot_implicit.png",
                "eval": "1",
                "eval_wait": 2500,
                "wait": ".o_pivot",
                "highlight": [".o_pivot tbody tr:nth-child(2) th", ".o_pivot_measure_row"],
                "settle": 2500,
            },
            {
                "url": pivot,
                "name": "03_filtre_grupari.png",
                "wait": ".o_pivot",
                "eval": open_search,
                "eval_wait": 1500,
                "settle": 2000,
            },
            {
                "url": pivot,
                "name": "04_pivot_citire.png",
                "eval": "1",
                "eval_wait": 2500,
                "wait": ".o_pivot",
                "highlight": [".o_pivot_measure_row", ".o_pivot tbody tr:first-child td"],
                "settle": 2500,
            },
            {
                "url": f"action={act}&view_type=list",
                "name": "05_lista_pozitii.png",
                "eval": "1",
                "eval_wait": 2500,
                "wait": ".o_list_view",
                "settle": 2500,
            },
            {
                "url": pivot,
                "name": "06_export_pivot.png",
                "wait": ".o_pivot",
                "eval": (
                    "(() => { let e = document.querySelector('button.o_pivot_download');"
                    " while (e && e !== document.body) { e.style.overflow = 'visible'; e = e.parentElement; } })()"
                ),
                "eval_wait": 2500,
                "highlight": "button.o_pivot_download",
                "settle": 2500,
            },
            {
                "url": f"action={act}&view_type=list",
                "name": "07_export_lista.png",
                "wait": ".o_list_view",
                "eval": select_all,
                "eval_wait": 1500,
                "highlight": ".o_cp_action_menus .dropdown-toggle",
                "settle": 2000,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")
