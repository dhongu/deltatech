# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Acces pe echipa de vânzări și depozit implicit" —
# generate în timpul testelor, pe compania „RO Company" în RON, în română pentru fișă.
#
# Seedează două depozite și două echipe (București, Cluj), doi agenți, un șef de echipă
# (București) și comenzi pe fiecare echipă; capturile se fac cu utilizatorul potrivit fiecărui pas.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_sale_team,l10n_ro,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import new_test_user, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# Fila „Alte informații" a comenzii (echipa și depozitul stau acolo)
READY_FORM = ".o_form_view"


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSaleTeamScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_sale_team"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Retail SRL")
        company = cls.env.company
        env = cls.env(su=True)
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        ro = env.ref("base.ro")

        # depozite
        wh_buc = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        wh_buc.write({"name": "Depozit București", "code": "BUC"})
        wh_cluj = env["stock.warehouse"].create({"name": "Depozit Cluj", "code": "CLJ", "company_id": company.id})

        # echipe: le curățăm pe cele implicite, ca lista să conțină doar echipele de demo
        env["crm.team"].search([]).write({"active": False})
        cls.team_buc = env["crm.team"].create({"name": "Magazin București", "warehouse_id": wh_buc.id})
        cls.team_cluj = env["crm.team"].create({"name": "Magazin Cluj", "warehouse_id": wh_cluj.id})

        # utilizatori (parola = login, cum cere mixinul)
        common = {"company_id": company.id, "company_ids": [Command.set([company.id])], "lang": "ro_RO"}
        cls.agent_buc = new_test_user(
            env,
            login="mihai.popescu",
            name="Mihai Popescu",
            groups="base.group_user,sales_team.group_sale_salesman",
            **common,
        )
        cls.agent_cluj = new_test_user(
            env,
            login="ioana.rusu",
            name="Ioana Rusu",
            groups="base.group_user,sales_team.group_sale_salesman",
            **common,
        )
        cls.manager_buc = new_test_user(
            env,
            login="andrei.ionescu",
            name="Andrei Ionescu",
            groups="base.group_user,deltatech_sale_team.group_sale_team_manager",
            **common,
        )
        for user, team in (
            (cls.agent_buc, cls.team_buc),
            (cls.manager_buc, cls.team_buc),
            (cls.agent_cluj, cls.team_cluj),
        ):
            env["crm.team.member"].create({"crm_team_id": team.id, "user_id": user.id})

        # arhivăm clienții din datele demo ale bazei, ca listele să conțină doar clienții seedați
        keep = env["res.company"].search([]).partner_id
        env["res.partner"].search([("user_ids", "=", False), ("id", "not in", keep.ids)]).write({"active": False})

        # clienți: ai agentului din București, ai agentului din Cluj, fără vânzător
        def partner(name, user=False):
            return env["res.partner"].create(
                {"name": name, "country_id": ro.id, "user_id": user.id if user else False, "company_id": False}
            )

        cls.cust_buc1 = partner("Alfa Construct SRL", cls.agent_buc)
        cls.cust_buc2 = partner("Beta Instal SRL", cls.agent_buc)
        cls.cust_cluj = partner("Gama Mobilier SRL", cls.agent_cluj)
        cls.cust_cluj2 = partner("Delta Textile SRL", cls.agent_cluj)
        cls.cust_free = partner("Omega Retail SRL")

        product = env["product.product"].create(
            {
                "name": "Birou ergonomic",
                "type": "consu",
                "invoice_policy": "order",
                "list_price": 1200.0,
                "company_id": company.id,
            }
        )

        def order(partner, user, team, qty, confirm=True):
            so = env["sale.order"].create(
                {
                    "partner_id": partner.id,
                    "user_id": user.id if user else False,
                    "team_id": team.id if team else False,
                    "warehouse_id": team.warehouse_id.id if team else wh_buc.id,
                    "order_line": [Command.create({"product_id": product.id, "product_uom_qty": qty})],
                }
            )
            if confirm:
                so.action_confirm()
            return so

        order(cls.cust_buc1, cls.agent_buc, cls.team_buc, 3)
        order(cls.cust_buc2, cls.agent_buc, cls.team_buc, 5)
        order(cls.cust_buc1, cls.manager_buc, cls.team_buc, 2)
        order(cls.cust_cluj, cls.agent_cluj, cls.team_cluj, 4)
        order(cls.cust_cluj2, cls.agent_cluj, cls.team_cluj, 6)
        order(cls.cust_free, False, False, 1)
        cls.quote_cluj = order(cls.cust_cluj, cls.agent_cluj, cls.team_cluj, 2, confirm=False)

        # factură pe echipa București și una pe Cluj (lista facturilor șefului de echipă)
        for so in env["sale.order"].search([("state", "=", "sale")]):
            if so.invoice_status == "to invoice":
                inv = so._create_invoices()
                inv.action_post()

        # listă de comenzi grupată pe echipă (pasul 3)
        cls.action_grouped = env["ir.actions.act_window"].create(
            {
                "name": "Comenzi",
                "res_model": "sale.order",
                "view_mode": "list,form",
                "view_id": env.ref("sale.view_order_tree").id,
                "domain": [("state", "in", ("sale", "done"))],
                "context": {"group_by": ["team_id"]},
            }
        )
        cls.action_grouped.update_field_translations("name", {"ro_RO": "Comenzi pe echipe"})
        env.flush_all()

    def _shots_admin(self):
        return [
            # 1. formularul echipei, cu Depozitul implicit
            {
                "url": f"id={self.team_cluj.id}&model=crm.team&view_type=form",
                "name": "01_echipa_depozit.png",
                "wait": READY_FORM,
                "highlight": ["div[name='warehouse_id']"],
                "settle": 2000,
            },
        ]

    def _shots_agent_cluj(self):
        return [
            # 2. oferta agentului din Cluj: echipa și depozitul preluat din echipă
            {
                "url": f"id={self.quote_cluj.id}&model=sale.order&view_type=form",
                "name": "02_comanda_depozit.png",
                "wait": READY_FORM,
                "click_tab": "Other Info",
                "highlight": ["div[name='team_id']", "div[name='warehouse_id']"],
                "settle": 2000,
            },
            # 3. comenzile agentului: doar ale lui și cele fără vânzător
            {
                "url": "action=sale.action_orders&view_type=list",
                "name": "03_comenzi_agent.png",
                "wait": ".o_list_view",
                "settle": 2000,
            },
            # 4. clienții agentului: ai lui și cei fără vânzător
            {
                "url": "action=account.res_partner_action_customer&view_type=list",
                "name": "04_clienti_agent.png",
                "wait": ".o_list_view",
                "settle": 2000,
            },
        ]

    def _shots_manager(self):
        return [
            # 5. comenzile șefului de echipă, grupate pe echipă
            {
                "url": f"action={self.action_grouped.id}&view_type=list",
                "name": "05_lista_sef_echipa.png",
                "wait": ".o_list_view",
                "settle": 2000,
            },
            # 6. analiza vânzărilor: doar cifrele echipei lui
            {
                "url": "action=sale.action_order_report_all&view_type=list",
                "name": "06_analiza_vanzari_sef.png",
                "wait": ".o_list_view, .o_pivot, .o_graph_renderer",
                "settle": 3000,
            },
            # 7. facturile șefului de echipă
            {
                "url": "action=account.action_move_out_invoice_type&view_type=list",
                "name": "07_facturi_sef.png",
                "wait": ".o_list_view",
                "settle": 2000,
            },
            # 8. echipele de vânzări: doar echipa proprie
            {
                "url": "action=sales_team.crm_team_action_config&view_type=list",
                "name": "08_echipe_sef.png",
                "wait": ".o_list_view",
                "settle": 2000,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots_admin())
        self.capture_screenshots(self._shots_agent_cluj(), login="ioana.rusu")
        self.capture_screenshots(self._shots_manager(), login="andrei.ionescu")
