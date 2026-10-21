# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Schimbarea unității de măsură a unui produs folosit
# deja în documente" — generate în timpul testelor, în limba RO, pe compania
# „Demo UM SRL" în RON.
#
# Seedează două produse de cherestea create greșit în Unități. Primul rămâne
# neschimbat (meniul Acțiune și asistentul). Al doilea are o achiziție recepționată
# și facturată și o vânzare livrată și facturată, toate postate (cazul în care Odoo
# standard nu mai permite schimbarea), și e trecut prin asistent în m³, cu unitatea
# de achiziție m³ (produsul, comanda de achiziție, factura și mișcările după schimbare).
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_change_uom,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# Deschide meniul „Acțiune" (rotița) din formularul produsului.
OPEN_ACTION_MENU = """
    [...document.querySelectorAll('.o_cp_action_menus button')]
        .find((b) => b.querySelector('.fa-cog')).click();
"""

# Deschide meniul „Acțiune" și alege „Schimbă UM", ca să apară asistentul.
OPEN_WIZARD = """
    new Promise((resolve) => {
        [...document.querySelectorAll('.o_cp_action_menus button')]
            .find((b) => b.querySelector('.fa-cog')).click();
        setTimeout(() => {
            [...document.querySelectorAll('.o-dropdown--menu .dropdown-item')]
                .find((i) => i.textContent.includes('Schimbă UM')).click();
            resolve();
        }, 800);
    })
"""

# Tab-ul „Achiziție" din formularul produsului, unde stă unitatea implicită de achiziție.
OPEN_PURCHASE_TAB = """
    [...document.querySelectorAll('.o_notebook a.nav-link')]
        .find((a) => a.textContent.includes('Achizi')).click();
"""

# Pe factură, coloana „Unitate" e opțională și ascunsă implicit: o afișăm din meniul coloanelor.
SHOW_INVOICE_UOM = """
    new Promise((resolve) => {
        document.querySelector('.o_field_one2many .o_optional_columns_dropdown_toggle').click();
        setTimeout(() => {
            const input = [...document.querySelectorAll('.o-dropdown--menu input[type=checkbox]')]
                .find((i) => i.closest('.dropdown-item, label, span').textContent.includes('Unitate'));
            if (input && !input.checked) input.click();
            document.body.click();
            setTimeout(resolve, 800);
        }, 800);
    })
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestChangeUomScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_change_uom"

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
        for xmlid in ("uom.group_uom", "purchase.group_purchase_manager", "sales_team.group_sale_manager"):
            group = env.ref(xmlid)
            env.user.group_ids = [Command.link(group.id)]
            admin.group_ids = [Command.link(group.id)]
        env["res.config.settings"].create({"group_uom": True}).execute()
        env.flush_all()

        cls.uom_unit = env.ref("uom.product_uom_unit")
        cls.uom_m3 = env.ref("uom.product_uom_cubic_meter")
        cls.customer = env["res.partner"].create({"name": "Construct Casa SRL", "country_id": env.ref("base.ro").id})
        cls.vendor = env["res.partner"].create({"name": "Gater Bistrița SRL", "country_id": env.ref("base.ro").id})

        # nume în română pentru depozit, recepții și lista de prețuri (create înaintea limbii RO)
        cls.warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        cls.warehouse.write({"name": "Depozit central", "code": "WH"})
        cls.warehouse.in_type_id.name = "Recepții"
        cls.warehouse.out_type_id.name = "Livrări"
        env["product.pricelist"].search([]).write({"name": "Listă de prețuri RON"})

        cls.product_before = cls._product("Cherestea brad 50x100")
        cls.product_after = cls._product("Cherestea molid 50x100")
        cls._orders(cls.product_before)
        cls.sale_after, cls.purchase_after = cls._orders(cls.product_after)

        # achiziția: confirmată, recepționată și facturată
        cls.purchase_after.button_confirm()
        cls._validate(cls.purchase_after.picking_ids)
        cls.purchase_after.action_create_invoice()
        cls.bill_after = cls.purchase_after.invoice_ids
        cls.bill_after.invoice_date = cls.bill_after.date
        cls.bill_after.action_post()
        # vânzarea: confirmată, livrată și facturată
        cls.sale_after.action_confirm()
        cls._validate(cls.sale_after.picking_ids)
        cls.invoice_after = cls.sale_after._create_invoices()
        cls.invoice_after.action_post()

        # schimbarea pe al doilea produs: din Unități în m³, cu unitatea de achiziție m³
        wizard = (
            env["product.change.uom"]
            .with_context(active_id=cls.product_after.id)
            .create({"uom_id": cls.uom_m3.id, "purchase_uom_id": cls.uom_m3.id})
        )
        wizard.with_context(active_id=cls.product_after.id).do_change()

        cls.action_moves = env["ir.actions.act_window"].create(
            {
                "name": "Istoric mișcări",
                "res_model": "stock.move.line",
                "view_mode": "list",
                "view_id": env.ref("stock.view_move_line_tree").id,
                "domain": [("product_id", "=", cls.product_after.product_variant_id.id)],
            }
        )

    @classmethod
    def _validate(cls, pickings):
        for move in pickings.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        pickings.button_validate()

    @classmethod
    def _product(cls, name):
        return cls.env["product.template"].create(
            {
                "name": name,
                "company_id": cls.env.company.id,
                "is_storable": True,
                "uom_id": cls.uom_unit.id,
                "list_price": 1450.0,
                "standard_price": 1100.0,
                "seller_ids": [Command.create({"partner_id": cls.vendor.id, "price": 1100.0})],
            }
        )

    @classmethod
    def _orders(cls, product):
        variant = product.product_variant_id
        sale = cls.env["sale.order"].create(
            {
                "partner_id": cls.customer.id,
                "order_line": [Command.create({"product_id": variant.id, "product_uom_qty": 2.0})],
            }
        )
        purchase = cls.env["purchase.order"].create(
            {
                "partner_id": cls.vendor.id,
                "order_line": [Command.create({"product_id": variant.id, "product_qty": 4.5})],
            }
        )
        return sale, purchase

    def test_capture_fise(self):
        before = f"id={self.product_before.id}&model=product.template&view_type=form"
        after = f"id={self.product_after.id}&model=product.template&view_type=form"
        self.capture_screenshots(
            [
                # 1. meniul Acțiune din formularul produsului, cu „Schimbă UM"
                {
                    "url": before,
                    "name": "01_produs_actiune_schimba_um.png",
                    "wait": ".o_form_view",
                    "eval": OPEN_ACTION_MENU,
                    "highlight": [".o-dropdown--menu .dropdown-item:has-text('Schimbă UM')"],
                    "settle": 2000,
                },
                # 2. asistentul, cu unitatea produsului și unitatea implicită de achiziție
                {
                    "url": before,
                    "name": "02_asistent_schimba_um.png",
                    "wait": ".o_form_view",
                    "eval": OPEN_WIZARD,
                    "eval_wait": 2500,
                    "highlight": [
                        ".modal div[name='uom_id']",
                        ".modal div[name='purchase_uom_id']",
                        ".modal button[name='do_change']",
                    ],
                    "settle": 2000,
                },
                # 3. produsul după schimbare: unitatea m³ și unitatea implicită de achiziție m³
                {
                    "url": after,
                    "name": "03_produs_dupa_schimbare.png",
                    "wait": ".o_form_view",
                    "eval": OPEN_PURCHASE_TAB,
                    "highlight": ["div[name='purchase_uom_id']"],
                    "settle": 2000,
                },
                # 4. comanda de achiziție recepționată și facturată, trecută în m³
                {
                    "url": f"id={self.purchase_after.id}&model=purchase.order&view_type=form",
                    "name": "04_comanda_achizitie_dupa.png",
                    "wait": ".o_form_view",
                    "highlight": [".o_field_one2many td[name='product_uom_id']"],
                    "settle": 2000,
                },
                # 5. factura de client postată, cu linia trecută în m³
                {
                    "url": f"id={self.invoice_after.id}&model=account.move&view_type=form",
                    "name": "05_factura_client_dupa.png",
                    "wait": ".o_form_view",
                    "eval": SHOW_INVOICE_UOM,
                    "eval_wait": 2500,
                    "highlight": [".o_field_one2many td[name='product_uom_id']"],
                    "settle": 2000,
                },
                # 6. mișcările de stoc ale produsului (recepție și livrare), în m³
                {
                    "url": f"action={self.action_moves.id}",
                    "name": "06_miscari_stoc_dupa.png",
                    "wait": ".o_list_view",
                    "highlight": ["td[name='product_uom_id']"],
                    "settle": 2000,
                },
            ],
            hide_systray=True,
        )
