# © 2026 Terrabit Solutions
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa consultant „Tipuri de documente" — generate în timpul testelor, în RO.
#
# Rulare (bază nouă; fără l10n_ro testul se sare tăcut, cu „0 tests"):
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i l10n_ro,deltatech_record_type,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import SUPERUSER_ID, Command
from odoo.tests import Form, tagged

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
        # facturare la cantitatea comandată: factura de furnizor se generează fără recepție
        cls.product = env["product.product"].create(
            {"name": "Produs demo", "type": "consu", "list_price": 100.0, "purchase_method": "purchase"}
        )
        term = env.ref("account.account_payment_term_30days", raise_if_not_found=False) or env[
            "account.payment.term"
        ].search([], limit=1)
        route = env["stock.route"].create({"name": "Livrare directă", "sale_selectable": True})
        # denumiri lizibile în capturi (în loc de cele tehnice ale bazei de test)
        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        if warehouse:
            # altfel „Livrare la" afișează numele tehnic al depozitului („company_1_data: Recepții")
            warehouse.write({"name": "Depozit central", "code": "DC"})
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
        # al doilea jurnal de achiziții: tipul „Achiziție import" îl completează pe comandă,
        # iar comanda îl transmite facturii de furnizor (purchase.py, _prepare_invoice)
        cls.journal_import = env["account.journal"].create(
            {"name": "Achiziții import", "code": "AIMP", "type": "purchase", "company_id": company.id}
        )
        f_journal = env["ir.model.fields"]._get("purchase.order", "journal_id")
        cls.type_purchase = env["record.type"].create(
            {
                "name": "Achiziție import",
                "model": "purchase.order",
                "default_values_ids": [
                    Command.create(
                        {
                            "field_id": f_journal.id,
                            "field_name": "journal_id",
                            "field_value": str(cls.journal_import.id),
                            "field_type": "id",
                        }
                    )
                ],
            }
        )
        cls.type_invoice = env["record.type"].create({"name": "Factură servicii", "model": "account.move"})

        # comandă de vânzare cu tip, prin formular: onchange-ul tipului aplică valorile implicite
        so_form = Form(env["sale.order"])
        so_form.partner_id = cls.partner
        so_form.so_type = cls.type_wholesale
        so_form.user_id = admin
        with so_form.order_line.new() as so_line:
            so_line.product_id = cls.product
            so_line.product_uom_qty = 10
            so_line.price_unit = 100.0
        cls.so_typed = so_form.save()
        cls.term = term
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
        # comandă de achiziție cu tip, prin formular: jurnalul vine din valorile implicite ale tipului
        po_form = Form(env["purchase.order"])
        po_form.partner_id = cls.supplier
        po_form.po_type = cls.type_purchase
        po_form.user_id = admin
        with po_form.order_line.new() as po_line:
            po_line.product_id = cls.product
            po_line.product_qty = 5
            po_line.price_unit = 60.0
        cls.po = po_form.save()
        # confirmare + factură de furnizor generată din comandă, în jurnalul comenzii
        cls.po.button_confirm()
        cls.po.action_create_invoice()
        cls.bill = cls.po.invoice_ids
        cls.bill.invoice_date = cls.bill.date  # altfel câmpul obligatoriu apare gol, cu roșu
        # factură de client (ciornă) cu tip
        cls.invoice = env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner.id,
                "invoice_type": cls.type_invoice.id,
                "invoice_user_id": admin.id,
                "invoice_line_ids": [
                    Command.create({"name": "Servicii de consultanță", "quantity": 1, "price_unit": 1000.0})
                ],
            }
        )
        cls.act_sale_types = env.ref("deltatech_record_type.action_sale_order_type").id
        cls.act_orders = env.ref("sale.action_orders").id
        env.flush_all()

    def test_capture_fise(self):
        # datele din capturi provin din fluxul real (onchange-ul tipului, _prepare_invoice)
        self.assertEqual(self.so_typed.client_order_ref, "Comandă en-gros")
        self.assertEqual(self.so_typed.payment_term_id, self.term)
        self.assertEqual(self.po.journal_id, self.journal_import)
        self.assertEqual(self.bill.move_type, "in_invoice")
        self.assertEqual(self.bill.journal_id, self.journal_import)
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
                # 2. Valorile implicite ale tipului — doar notebook-ul (mixinul nu are clip pe
                # selector: ascundem restul ecranului, iar autotrim decupează fundalul rămas)
                {
                    "url": f"id={self.type_wholesale.id}&model=record.type&view_type=form",
                    "name": "02_valori_implicite.png",
                    "wait": ".o_form_view .o_notebook",
                    "eval": """() => {
                        // „important": bara de control are clase Bootstrap d-flex (!important)
                        const hide = (e) => e.style.setProperty('display', 'none', 'important');
                        document.querySelectorAll('.o_main_navbar, .o_control_panel').forEach(hide);
                        const nb = document.querySelector('.o_form_sheet .o_notebook');
                        [...nb.parentElement.children].forEach((e) => { if (e !== nb) { hide(e); } });
                        // bulinele numerotate de pe antetul tabelului nu trebuie tăiate
                        document.querySelectorAll('.o_notebook, .o_notebook *').forEach((e) => {
                            e.style.overflow = 'visible';
                        });
                    }""",
                    "eval_wait": 500,
                    "settle": 2000,
                    "highlight": [
                        "th[data-name='value_ref'], td[name='value_ref']",
                        "th[data-name='field_value'], td[name='field_value']",
                    ],
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
                # 6. Comanda de achiziție cu tip și jurnalul „Achiziții import" (tab „Alte informații")
                {
                    "url": f"id={self.po.id}&model=purchase.order&view_type=form",
                    "name": "06_comanda_achizitie_tip.png",
                    "wait": ".o_form_view",
                    "click_tab": "Other Info",
                    "settle": 2500,
                    # „Receipt Status" nu are traducere RO în modulul purchase și nu ține de fișă
                    "hide_fields": ["receipt_status"],
                    "highlight": ["div[name='po_type']", "div[name='journal_id']"],
                    "full": True,
                },
                # 9. Factura de furnizor generată din comandă, în jurnalul comenzii
                {
                    "url": f"id={self.bill.id}&model=account.move&view_type=form",
                    "name": "09_factura_furnizor_jurnal.png",
                    "wait": ".o_form_view",
                    "settle": 2500,
                    "highlight": ["div[name='journal_div']"],
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
