# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Stocul disponibil al furnizorului între companii",
# generate în timpul testelor: în RO pentru fișă și în EN (static/description/en/) pentru
# readme/USAGE.md.
#
# Seed: firma furnizoare „Furnizor Grup SRL" (compania testului) are 20 de pompe în stoc;
# firma care vinde, „Distribuitor Grup SRL", are pe produs o linie de furnizor cu partenerul
# firmei furnizoare. În firma furnizoare se validează o livrare de 5 bucăți și se rezervă una de
# 3 bucăți, deci linia de furnizor arată 12 bucăți libere. Capturile din firma care vinde le face
# un utilizator al ei („vanzari"); cele din firma furnizoare, administratorul.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_inter_company_vendor_stock,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import new_test_user, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# Coloana „Cantitate disponibilă la furnizor" e opțională și ascunsă pe liniile comenzii: o afișăm.
SHOW_VENDOR_QTY = """
    new Promise((resolve) => {
        document.querySelector('.o_field_one2many .o_optional_columns_dropdown_toggle').click();
        setTimeout(() => {
            const input = [...document.querySelectorAll('.o-dropdown--menu input[type=checkbox]')]
                .find((i) => i.closest('.dropdown-item, label, span').textContent.includes('%(label)s'));
            if (input && !input.checked) input.click();
            document.body.click();
            setTimeout(() => {
                // lista își fixează lățimile coloanelor: lărgim coloana ca antetul să nu fie trunchiat
                document.head.insertAdjacentHTML('beforeend',
                    '<style>th[data-name="vendor_qty_available"]{width:250px!important;min-width:250px!important}</style>');
                resolve();
            }, 800);
        }, 800);
    })
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestInterCompanyVendorStockScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_inter_company_vendor_stock"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Furnizor Grup SRL")
        env = cls.env
        cls.vendor_company = env.company
        ro = env.ref("base.ro")
        cls.selling_company = env["res.company"].create(
            {"name": "Distribuitor Grup SRL", "country_id": ro.id, "currency_id": env.ref("base.RON").id}
        )
        companies = cls.vendor_company | cls.selling_company
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(c.id) for c in companies], "company_id": cls.vendor_company.id})
        env.user.company_ids = [Command.link(c.id) for c in companies]
        cls.seller_user = new_test_user(
            env,
            login="vanzari",
            name="Ana Popescu",
            groups="base.group_user,sales_team.group_sale_salesman_all_leads,stock.group_stock_user",
            company_id=cls.selling_company.id,
            company_ids=[Command.set(companies.ids)],
        )

        cls.warehouse = env["stock.warehouse"].search([("company_id", "=", cls.vendor_company.id)], limit=1)
        cls.warehouse.write({"name": "Depozit furnizor", "code": "WH"})
        cls.warehouse.out_type_id.name = "Livrări"
        cls.customer_location = env.ref("stock.stock_location_customers")

        cls.template = env["product.template"].create(
            {
                "name": "Pompă submersibilă 1 CP",
                "is_storable": True,
                "company_id": False,
                "list_price": 1200.0,
                "standard_price": 850.0,
            }
        )
        cls.product = cls.template.product_variant_id
        # linia de furnizor din firma care vinde, cu firma furnizoare ca furnizor (doar pe produs)
        cls.vendor_line = env["product.supplierinfo"].create(
            {
                "partner_id": cls.vendor_company.partner_id.id,
                "product_tmpl_id": cls.template.id,
                "company_id": cls.selling_company.id,
                "product_code": "PS-1CP",
                "price": 850.0,
            }
        )
        env["stock.quant"]._update_available_quantity(cls.product, cls.warehouse.lot_stock_id, 20)

        # în firma furnizoare: o livrare de 5 bucăți validată, apoi una de 3 bucăți rezervată
        cls.picking_done = cls._picking(5)
        for move in cls.picking_done.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        cls.picking_done.button_validate()
        cls.picking_reserved = cls._picking(3)

        # în firma care vinde: oferta către client, cu stocul furnizorului pe linie
        cls.customer = env["res.partner"].create({"name": "Instal Expert SRL", "country_id": ro.id})
        cls.sale = (
            env["sale.order"]
            .with_user(cls.seller_user)
            .with_company(cls.selling_company)
            .create(
                {
                    "partner_id": cls.customer.id,
                    "company_id": cls.selling_company.id,
                    "order_line": [Command.create({"product_id": cls.product.id, "product_uom_qty": 2.0})],
                }
            )
        )

    @classmethod
    def _picking(cls, qty):
        location = cls.warehouse.lot_stock_id
        picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.warehouse.out_type_id.id,
                "partner_id": cls.selling_company.partner_id.id,
                "location_id": location.id,
                "location_dest_id": cls.customer_location.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom": cls.product.uom_id.id,
                            "product_uom_qty": qty,
                            "location_id": location.id,
                            "location_dest_id": cls.customer_location.id,
                        }
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        return picking

    def _vendor_shots(self):
        """Capturile din firma furnizoare (administratorul)."""
        return [
            # 2. livrarea rezervată în firma furnizoare
            {
                "url": f"id={self.picking_reserved.id}&model=stock.picking&view_type=form",
                "name": "02_rezervare.png",
                "wait": ".o_form_view",
                "highlight": [".o_statusbar_status"],
                "settle": 2000,
            },
            # 3. livrarea validată în firma furnizoare
            {
                "url": f"id={self.picking_done.id}&model=stock.picking&view_type=form",
                "name": "03_validare.png",
                "wait": ".o_form_view",
                "highlight": [".o_statusbar_status"],
                "settle": 2000,
            },
        ]

    def _seller_shots(self):
        """Capturile din firma care vinde (utilizatorul „vanzari")."""
        return [
            # 1. linia de furnizor, cu firma furnizoare și Cantitate disponibilă
            {
                "url": f"id={self.vendor_line.id}&model=product.supplierinfo&view_type=form",
                "name": "01_linie_furnizor.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='partner_id']", "div[name='qty_available']"],
                "settle": 2000,
            },
            # 4. oferta de vânzare, cu stocul furnizorului pe linie
            {
                "url": f"id={self.sale.id}&model=sale.order&view_type=form",
                "name": "04_comanda_vanzare.png",
                "wait": ".o_form_view",
                "eval": {
                    "ro_RO": SHOW_VENDOR_QTY % {"label": "Cantitate disponibilă la furnizor"},
                    "en_US": SHOW_VENDOR_QTY % {"label": "Vendor Quantity Available"},
                },
                "eval_wait": 2500,
                "highlight": [".o_field_one2many td[name='vendor_qty_available']"],
                "settle": 2000,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._vendor_shots(), hide_systray=True)
        self.capture_screenshots(self._seller_shots(), login="vanzari", hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._vendor_shots(), hide_systray=True, lang="en_US")
        self.capture_screenshots(self._seller_shots(), login="vanzari", hide_systray=True, lang="en_US")
