# © 2026 Terrabit Solutions
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa consultant „Tipuri de documente" — generate în timpul testelor, în RO.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_record_type,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import SUPERUSER_ID, Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestRecordTypeScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_record_type"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Tipuri SRL")
        company = cls.env.company
        # utilizatorul implicit de test nu are drepturi de vânzări; rămânem în compania RO
        cls.env = cls.env(user=SUPERUSER_ID, context=dict(cls.env.context, allowed_company_ids=[company.id]))
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [(4, company.id)], "company_id": company.id})
        # câmpul „Rute" de pe tip apare doar cu grupul „Trasee în mai mulți pași"
        for xmlid in (
            "stock.group_adv_location",
            "sales_team.group_sale_manager",
            "purchase.group_purchase_manager",
            "account.group_account_invoice",
        ):
            admin.group_ids = [(4, env.ref(xmlid).id)]

        cls.partner = env["res.partner"].create({"name": "Client Demo SRL", "country_id": env.ref("base.ro").id})
        cls.supplier = env["res.partner"].create({"name": "Furnizor Demo SRL", "country_id": env.ref("base.ro").id})
        cls.product = env["product.product"].create({"name": "Produs demo", "type": "consu", "list_price": 100.0})
        term = env.ref("account.account_payment_term_30days", raise_if_not_found=False) or env[
            "account.payment.term"
        ].search([], limit=1)
        route = env["stock.route"].create({"name": "Livrare directă", "sale_selectable": True})
        # denumiri lizibile în capturi (în loc de cele tehnice ale bazei de test)
        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        if warehouse:
            warehouse.in_type_id.name = "Recepții"
        pricelist = env["product.pricelist"].create(
            {"name": "Listă de prețuri RON", "currency_id": company.currency_id.id}
        )
        cls.partner.property_product_pricelist = pricelist

        f_ref = env["ir.model.fields"]._get("sale.order", "client_order_ref")
        f_term = env["ir.model.fields"]._get("sale.order", "payment_term_id")

        # tip de vânzare cu valori implicite (textul se scrie între apostrofuri — se evaluează cu safe_eval)
        cls.type_wholesale = env["record.type"].create(
            {
                "name": "Vânzare en-gros",
                "model": "sale.order",
                "route_ids": [Command.set(route.ids)],
                "default_values_ids": [
                    Command.create(
                        {
                            "field_id": f_ref.id,
                            "field_name": "client_order_ref",
                            "field_value": "'Comandă en-gros'",
                            "field_type": "char",
                        }
                    ),
                    Command.create(
                        {
                            "field_id": f_term.id,
                            "field_name": "payment_term_id",
                            "field_value": str(term.id),
                            "field_type": "id",
                        }
                    ),
                ],
            }
        )
        cls.type_retail = env["record.type"].create({"name": "Vânzare retail", "model": "sale.order"})
        cls.type_purchase = env["record.type"].create({"name": "Achiziție import", "model": "purchase.order"})
        cls.type_invoice = env["record.type"].create({"name": "Factură avans", "model": "account.move"})

        # comandă de vânzare cu tip (valorile implicite aplicate ca după onchange)
        line = Command.create({"product_id": cls.product.id, "product_uom_qty": 10, "price_unit": 100.0})
        cls.so_typed = env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "so_type": cls.type_wholesale.id,
                "client_order_ref": "Comandă en-gros",
                "payment_term_id": term.id,
                "user_id": admin.id,
                "order_line": [line],
            }
        )
        # comenzi confirmate, pentru grupare
        for type_, qty in ((cls.type_wholesale, 20), (cls.type_retail, 2)):
            order = env["sale.order"].create(
                {
                    "partner_id": cls.partner.id,
                    "so_type": type_.id,
                    "order_line": [
                        Command.create({"product_id": cls.product.id, "product_uom_qty": qty, "price_unit": 100.0})
                    ],
                }
            )
            order.action_confirm()
        # comandă fără tip, pe care operatorul nu o poate confirma
        cls.so_untyped = env["sale.order"].create(
            {"partner_id": cls.partner.id, "order_line": [Command.create({"product_id": cls.product.id})]}
        )
        # utilizator fără dreptul de a confirma fără tip
        cls.operator = env["res.users"].create(
            {
                "name": "Operator Vânzări",
                "login": "operator_tip",
                "password": "operator_tip",
                "lang": "ro_RO",
                "company_id": company.id,
                "company_ids": [Command.set(company.ids)],
                "group_ids": [
                    Command.set([env.ref("base.group_user").id, env.ref("sales_team.group_sale_salesman").id])
                ],
            }
        )
        cls.so_untyped.user_id = cls.operator  # regula „Own Documents Only" pentru vânzători
        # comandă de achiziție cu tip și jurnal
        pj = env["account.journal"].search([("type", "=", "purchase"), ("company_id", "=", company.id)], limit=1)
        cls.po = env["purchase.order"].create(
            {
                "partner_id": cls.supplier.id,
                "po_type": cls.type_purchase.id,
                "user_id": admin.id,
                "journal_id": pj.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_qty": 5,
                            "price_unit": 60.0,
                            "name": cls.product.name,
                        }
                    )
                ],
            }
        )
        # factură de client (ciornă) cu tip
        cls.invoice = env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner.id,
                "invoice_type": cls.type_invoice.id,
                "invoice_user_id": admin.id,
                "invoice_line_ids": [Command.create({"name": "Avans comandă", "quantity": 1, "price_unit": 1000.0})],
            }
        )
        cls.act_sale_types = env.ref("deltatech_record_type.action_sale_order_type").id
        cls.act_orders = env.ref("sale.action_orders").id
        env.flush_all()

    def test_capture_fise(self):
        self.capture_screenshots(
            [
                # 1. Formularul tipului de vânzare
                {
                    "url": f"id={self.type_wholesale.id}&model=record.type&view_type=form",
                    "name": "01_tip_vanzare_formular.png",
                    "wait": ".o_form_view",
                    "settle": 2000,
                    "highlight": ["div[name='name']", "div[name='user_ids']"],
                    "full": True,
                },
                # 2. Valorile implicite ale tipului
                {
                    "url": f"id={self.type_wholesale.id}&model=record.type&view_type=form",
                    "name": "02_valori_implicite.png",
                    "wait": ".o_form_view",
                    "settle": 2000,
                    "full": True,
                },
                # 3. Lista tipurilor de vânzare
                {
                    "url": f"action={self.act_sale_types}&view_type=list",
                    "name": "03_lista_tipuri.png",
                    "wait": ".o_list_view",
                    "settle": 2000,
                },
                # 4. Comanda de vânzare cu tip
                {
                    "url": f"id={self.so_typed.id}&model=sale.order&view_type=form",
                    "name": "04_comanda_vanzare_tip.png",
                    "wait": ".o_form_view",
                    "settle": 2500,
                    "highlight": ["div[name='so_type']"],
                    "full": True,
                },
                # 6. Comanda de achiziție cu tip și jurnal (tab „Alte informații")
                {
                    "url": f"id={self.po.id}&model=purchase.order&view_type=form",
                    "name": "06_comanda_achizitie_tip.png",
                    "wait": ".o_form_view",
                    "click_tab": "Other Info",
                    "settle": 2500,
                    "highlight": ["div[name='po_type']", "div[name='journal_id']"],
                    "full": True,
                },
                # 7. Factura cu tip (tab „Alte informații")
                {
                    "url": f"id={self.invoice.id}&model=account.move&view_type=form",
                    "name": "07_factura_tip.png",
                    "wait": ".o_form_view",
                    "click_tab": "Other Info",
                    "settle": 2500,
                    "highlight": ["[name='invoice_type']"],
                    "full": True,
                },
                # 8. Comenzi de vânzare grupate pe tip
                {
                    "url": f"action={self.act_orders}&view_type=list",
                    "name": "08_grupare_pe_tip.png",
                    "wait": ".o_list_view",
                    "eval": """() => {
                        const t = document.querySelector('.o_searchview_dropdown_toggler');
                        t.click();
                        return new Promise((res) => setTimeout(() => {
                            const item = [...document.querySelectorAll('.o_dropdown_container .o_menu_item, '
                                + '.o-dropdown-item')].find((e) => e.textContent.trim() === 'Tip comandă');
                            if (item) { item.click(); }
                            t.click();
                            res();
                        }, 800));
                    }""",
                    "eval_wait": 2000,
                    "settle": 2000,
                },
            ]
        )
        # 5. Blocarea la confirmare — cu un utilizator care nu are dreptul de excepție
        self.capture_screenshots(
            [
                {
                    "url": f"id={self.so_untyped.id}&model=sale.order&view_type=form",
                    "name": "05_blocare_confirmare.png",
                    "wait": ".o_form_view",
                    "click_btn": "button[name='action_confirm']",
                    "wait_after": ".o_form_view",
                    "settle": 4000,
                },
            ],
            login="operator_tip",
        )
