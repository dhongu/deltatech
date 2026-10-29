# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Ținte de achiziție pe producător și categorie" — generate în
# timpul testelor, în limba RO, pe compania „Demo Distribuție SRL" în RON.
#
# Seed (anul 2026, ținta Nord Computers SRL în valoare):
#   - T1: factura Nord 10 × Laptop 14" la 2.800 + 5 × Docking USB-C la 300 = 29.500;
#     factura redistribuitorului IT Distribuție 5 × Laptop 14" la 2.900 = 14.500 (exclusă);
#     factura client 3 × Laptop 14" la 3.500 = 10.500 (vânzări);
#   - T2: factura Nord 4 × Laptop 14" = 11.200, notă de credit 1 × Laptop 14" = 2.800 → 8.400;
#   - ținte: T1 și T2 globale 30.000, T1 Laptopuri 25.000, T1 Accesorii 2.000.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i l10n_ro,deltatech_purchase_target \
#       --test-tags=fise_screenshots/deltatech_purchase_target --stop-after-init
import unittest
from datetime import date

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPurchaseTargetScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_purchase_target"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Distribuție SRL")
        company = cls.env.company
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        (admin | env.user).tz = "Europe/Bucharest"
        for xmlid in (
            "purchase.group_purchase_manager",
            "sales_team.group_sale_manager",
            "deltatech_sale_margin.group_sale_margin",
        ):
            group = env.ref(xmlid)
            admin.group_ids = [Command.link(group.id)]
            env.user.group_ids = [Command.link(group.id)]
        env.flush_all()

        # baza poate avea produse demo: le arhivăm, ca listele să arate doar produsele fluxului
        env["product.template"].sudo().search([]).active = False

        Partner = env["res.partner"]
        cls.nord = Partner.create({"name": "Nord Computers SRL", "is_company": True, "is_manufacturer": True})
        cls.reseller = Partner.create({"name": "IT Distribuție SRL", "is_company": True})
        cls.customer = Partner.create({"name": "Birotica Plus SRL", "is_company": True})

        Category = env["product.public.category"]
        cls.laptops = Category.create({"name": "Laptopuri"})
        cls.accessories = Category.create({"name": "Accesorii"})
        cls.docking = Category.create({"name": "Docking", "parent_id": cls.accessories.id})

        def product(name, cost, price, categs):
            return env["product.product"].create(
                {
                    "name": name,
                    "type": "consu",
                    "standard_price": cost,
                    "list_price": price,
                    "manufacturer_id": cls.nord.id,
                    # cu compania, prețul de vânzare se afișează în lei, nu în moneda bazei
                    "company_id": company.id,
                    "public_categ_ids": [Command.set(categs.ids)],
                }
            )

        cls.laptop = product('Laptop 14"', 2800, 3500, cls.laptops)
        cls.dock = product("Docking USB-C", 300, 450, cls.laptops | cls.docking)

        def invoice(move_type, partner, day, lines):
            move = env["account.move"].create(
                {
                    "move_type": move_type,
                    "partner_id": partner.id,
                    "invoice_date": day,
                    "date": day,
                    "invoice_line_ids": [
                        Command.create({"product_id": prod.id, "quantity": qty, "price_unit": price})
                        for prod, qty, price in lines
                    ],
                }
            )
            move.action_post()
            return move

        invoice("in_invoice", cls.nord, date(2026, 2, 10), [(cls.laptop, 10, 2800), (cls.dock, 5, 300)])
        invoice("out_invoice", cls.customer, date(2026, 2, 15), [(cls.laptop, 3, 3500)])
        invoice("in_invoice", cls.reseller, date(2026, 3, 15), [(cls.laptop, 5, 2900)])
        invoice("in_invoice", cls.nord, date(2026, 5, 12), [(cls.laptop, 4, 2800)])
        invoice("in_refund", cls.nord, date(2026, 5, 20), [(cls.laptop, 1, 2800)])

        # o comandă confirmată, ca analiza achizițiilor să aibă ce grupa pe producător
        order = env["purchase.order"].create(
            {
                "partner_id": cls.nord.id,
                "order_line": [Command.create({"product_id": cls.laptop.id, "product_qty": 6, "price_unit": 2800})],
            }
        )
        order.button_confirm()

        cls.target = env["purchase.target"].create(
            {
                "manufacturer_id": cls.nord.id,
                "year": 2026,
                "line_ids": [
                    Command.create({"quarter": "1", "target_value": 30000}),
                    Command.create({"quarter": "2", "target_value": 30000}),
                    Command.create({"quarter": "1", "public_categ_id": cls.laptops.id, "target_value": 25000}),
                    Command.create({"quarter": "1", "public_categ_id": cls.accessories.id, "target_value": 2000}),
                ],
            }
        )

        def line(quarter, categ=None):
            # numele acțiunilor deschise de butoane se traduc în limba utilizatorului
            return cls.target.with_context(lang="ro_RO").line_ids.filtered(
                lambda rec: rec.quarter == quarter and rec.public_categ_id == (categ or Category)
            )

        Action = env["ir.actions.act_window"]
        # raportul fără filtrul „Anul curent" (datele sunt pe 2026, capturile pot rula în alt an)
        cls.act_lines = env.ref("deltatech_purchase_target.action_purchase_target_line").copy(
            {"path": False, "context": "{'search_default_group_manufacturer': 1}"}
        )
        # ecranele deschise de butoanele de pe rând, ca acțiuni cu același domeniu
        purchases = line("2").action_view_purchases()
        cls.act_purchases = Action.create(
            {
                "name": purchases["name"],
                "res_model": "account.move.line",
                "view_mode": "list",
                "view_id": purchases["views"][0][0],
                "search_view_id": purchases["search_view_id"],
                "domain": repr(purchases["domain"]),
                "context": "{'create': False}",
            }
        )
        sales = line("1").action_view_sales()
        cls.act_sales = Action.create(
            {
                "name": sales["name"],
                "res_model": "sale.margin.report",
                "view_mode": "list,pivot",
                "view_id": env.ref("deltatech_sale_margin.view_sale_margin_report_list").id,
                "domain": repr(sales["domain"]),
            }
        )
        cls.act_cost = env.ref("deltatech_purchase_target.action_vendor_cost_compare").copy(
            {
                "path": False,
                "context": "{'search_default_supplier': 1, 'search_default_current': 1, "
                "'pivot_row_groupby': ['product_id'], 'pivot_column_groupby': ['partner_id'], "
                "'pivot_measures': ['price_average']}",
            }
        )
        cls.act_po_report = env.ref("purchase.action_purchase_order_report_all").copy(
            {
                "path": False,
                "view_mode": "pivot,graph",
                "context": "{'pivot_row_groupby': ['manufacturer_id'], "
                "'pivot_measures': ['qty_ordered', 'price_total']}",
            }
        )

    def test_capture_fise(self):
        self.env.flush_all()
        tmpl = self.laptop.product_tmpl_id
        self.capture_screenshots(
            [
                {
                    "url": f"id={tmpl.id}&model=product.template&view_type=form",
                    "name": "01_produs_producator.png",
                    "wait": ".o_form_view",
                    "highlight": ["div[name='manufacturer_id']"],
                    "settle": 2000,
                },
                {
                    "url": f"id={tmpl.id}&model=product.template&view_type=form",
                    "name": "02_produs_categorii_ecommerce.png",
                    "wait": ".o_form_view",
                    "click_tab": "Vânzări",
                    "highlight": ["div[name='public_categ_ids']"],
                    "settle": 2000,
                },
                {
                    "url": f"id={self.target.id}&model=purchase.target&view_type=form",
                    "name": "03_tinta_producator.png",
                    "wait": ".o_form_view",
                    "highlight": ["div[name='partner_ids']", "button[name='action_view_lines']"],
                    "settle": 2500,
                },
                {
                    "url": f"action={self.act_lines.id}&view_type=list",
                    "name": "04_realizat_vs_tinta.png",
                    "wait": ".o_list_view",
                    "eval": "() => document.querySelector('.o_group_header')?.click()",
                    "eval_wait": 2000,
                    "settle": 2000,
                },
                {
                    "url": f"action={self.act_purchases.id}&view_type=list",
                    "name": "05_linii_facturi_furnizor.png",
                    "wait": ".o_list_view",
                    "settle": 2000,
                },
                {
                    "url": f"action={self.act_sales.id}&view_type=list",
                    "name": "06_vanzari_aceleasi_produse.png",
                    "wait": ".o_list_view",
                    "settle": 2000,
                },
                {
                    "url": f"action={self.act_cost.id}&view_type=pivot",
                    "name": "07_comparatie_cost_furnizori.png",
                    "wait": ".o_pivot",
                    "settle": 2500,
                },
                {
                    "url": f"action={self.act_po_report.id}&view_type=pivot",
                    "name": "08_analiza_achizitii_producator.png",
                    "wait": ".o_pivot",
                    "settle": 2500,
                },
            ],
            hide_systray=True,
        )
