# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Amânarea livrării și starea coletului", în RO (fișa) și EN
# (readme/USAGE.md), pe planul de conturi românesc (`setup_country("ro")`).
#
# Seed: furnizorul de plată „Plată online cu cardul" cu Livrare amânată bifată, echipa de vânzări
# cu amânarea pentru plata prin transfer, comanda S00201 (4 scaune) confirmată, cu livrarea
# disponibilă, comanda S00202 (2 birouri) cu livrarea amânată și comanda S00203 (3 scaune) livrată,
# cu coletul „În tranzit" la curier.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i l10n_ro,deltatech_delivery_status,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import json
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


def _do_action(action):
    """JS: deschide o acțiune în locul ecranului curent."""
    options = json.dumps({"clearBreadcrumbs": True})
    return f"odoo.__WOWL_DEBUG__.root.env.services.action.doAction({json.dumps(action)}, {options})"


@tagged("-at_install", "post_install", "fise_screenshots")
class TestDeliveryStatusScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_delivery_status"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        env = cls.env
        cls.prepare_ro_company()
        company = env.company
        groups = [
            env.ref(xmlid).id
            for xmlid in (
                "sales_team.group_sale_manager",
                "stock.group_stock_manager",
                "account.group_account_manager",
                "base.group_system",
            )
        ]
        # utilizatorul testului face seed-ul, admin face capturile
        env.user.group_ids = [Command.link(group) for group in groups]
        env.ref("base.user_admin").write(
            {
                "company_ids": [Command.link(company.id)],
                "company_id": company.id,
                "name": "Maria Ionescu",
                "group_ids": [Command.link(group) for group in groups],
            }
        )

        cls.provider = env["payment.provider"].create(
            {
                "name": "Plată online cu cardul",
                "company_id": company.id,
                "postponed_delivery": True,
            }
        )
        cls.team = env["crm.team"].create(
            {"name": "Vânzări online", "company_id": company.id, "postpone_payment_transfer": True}
        )

        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        # depozitul companiei de test are nume tehnic (company_1_data / compa)
        warehouse.write({"name": "Depozit central", "code": "DC"})
        cls.out_type = warehouse.out_type_id
        cls.out_type.auto_batch = False
        for lang, name in (("ro_RO", "Livrări"), ("en_US", "Delivery Orders")):
            cls.out_type.with_context(lang=lang).name = name
        for lang, name in (("ro_RO", "Recepții"), ("en_US", "Receipts")):
            (cls.out_type.return_picking_type_id or warehouse.in_type_id).with_context(lang=lang).name = name

        product_vals = {"is_storable": True, "invoice_policy": "order"}
        cls.chair = env["product.product"].create(
            {"name": "Scaun ergonomic Nova", "list_price": 450.0, "standard_price": 300.0, **product_vals}
        )
        cls.desk = env["product.product"].create(
            {"name": "Birou reglabil Flex", "list_price": 1200.0, "standard_price": 800.0, **product_vals}
        )
        for product in cls.chair | cls.desk:
            env["stock.quant"]._update_available_quantity(product, warehouse.lot_stock_id, 50.0)

        ro = env.ref("base.ro").id
        cls.alfa, cls.gamma, cls.delta = env["res.partner"].create(
            [
                {"name": "Alfa Construct SRL", "country_id": ro, "lang": "ro_RO"},
                {"name": "Gamma Retail SRL", "country_id": ro, "lang": "ro_RO"},
                {"name": "Delta Office SRL", "country_id": ro, "lang": "ro_RO"},
            ]
        )

        # numerele fixe: secvențele comenzilor nu se anulează la rollback
        cls.order = cls._sale_order("S00201", cls.alfa, [(cls.chair, 4.0)])
        cls.picking = cls.order.picking_ids

        cls.order_postponed = cls._sale_order("S00202", cls.gamma, [(cls.desk, 2.0)])
        cls.order_postponed.postpone_delivery()
        cls.picking_postponed = cls.order_postponed.picking_ids

        cls.order_done = cls._sale_order("S00203", cls.delta, [(cls.chair, 3.0)])
        cls.picking_done = cls.order_done.picking_ids
        for move in cls.picking_done.move_ids:
            move.quantity = move.product_uom_qty
        cls.picking_done.move_ids.picked = True
        cls.picking_done.button_validate()
        # starea coletului o scrie integrarea cu curierul; aici e pusă direct
        cls.picking_done.delivery_state = "in_transit"
        env.flush_all()

    @classmethod
    def _sale_order(cls, name, partner, lines):
        order = cls.env["sale.order"].create(
            {
                "name": name,
                "partner_id": partner.id,
                "team_id": cls.team.id,
                "user_id": cls.env.ref("base.user_admin").id,
                "order_line": [Command.create({"product_id": p.id, "product_uom_qty": qty}) for p, qty in lines],
            }
        )
        order.action_confirm()
        return order

    def _order_url(self, order):
        return f"id={order.id}&model=sale.order&view_type=form"

    def _picking_url(self, picking):
        return f"id={picking.id}&model=stock.picking&view_type=form"

    def _shots_config(self):
        return [
            {
                "url": f"id={self.provider.id}&model=payment.provider&view_type=form",
                "name": "01_furnizor_plata_livrare_amanata.png",
                "wait": ".o_form_view div[name='postponed_delivery']",
                "highlight": ["div[name='postponed_delivery']"],
            },
            {
                "url": f"id={self.team.id}&model=crm.team&view_type=form",
                "name": "02_echipa_vanzari_transfer.png",
                "wait": ".o_form_view div[name='postpone_payment_transfer']",
                "highlight": ["div[name='postpone_payment_transfer']"],
            },
            {
                "url": f"id={self.out_type.id}&model=stock.picking.type&view_type=form",
                "name": "03_tip_operatie_amanat.png",
                "wait": ".o_form_view div[name='postponed']",
                "highlight": ["div[name='postponed']"],
            },
        ]

    def _shots_flow(self):
        orders = {
            "type": "ir.actions.act_window",
            "name": None,
            "res_model": "sale.order",
            "views": [[False, "list"], [False, "form"]],
            "domain": [["state", "=", "sale"]],
            "context": {"search_default_postponed_delivery": 1},
        }
        pickings = {
            "type": "ir.actions.act_window",
            "name": None,
            "res_model": "stock.picking",
            "views": [[False, "list"], [False, "form"]],
            "domain": [["picking_type_code", "=", "outgoing"]],
            "context": {"restricted_picking_type_code": "outgoing"},
        }
        return [
            {
                "url": self._order_url(self.order),
                "name": "04_comanda_buton_amana.png",
                "wait": ".o_form_view button[name='postpone_delivery']",
                "highlight": ["button[name='postpone_delivery']", "button[name='action_view_delivery']"],
            },
            {
                "url": self._picking_url(self.picking_postponed),
                "name": "05_livrare_amanata.png",
                "wait": ".o_form_view .ribbon",
                "highlight": [".ribbon", "div[name='postponed']"],
            },
            {
                "url": self._picking_url(self.picking_postponed),
                "name": "06_validare_refuzata.png",
                "wait": ".o_form_view button[name='button_validate']",
                "click_btn": "button[name='button_validate']",
                "wait_after": ".modal",
                "settle": 2000,
                "highlight": [".modal .modal-body"],
            },
            {
                "url": self._order_url(self.order),
                "name": "07_comenzi_filtru_amanate.png",
                "wait": ".o_form_view",
                "eval": {
                    lang: _do_action(dict(orders, name=name))
                    for lang, name in (("ro_RO", "Comenzi de vânzare"), ("en_US", "Sales Orders"))
                },
                "eval_wait": 2500,
                "highlight": [".o_searchview_facet", ".o_data_row td[name='name']"],
            },
            {
                "url": self._order_url(self.order_postponed),
                "name": "08_comanda_buton_elibereaza.png",
                "wait": ".o_form_view button[name='release_delivery']",
                "highlight": ["button[name='release_delivery']"],
            },
            {
                "url": self._picking_url(self.picking),
                "name": "09_livrari_disponibilitate.png",
                "wait": ".o_form_view",
                "eval": {
                    lang: _do_action(dict(pickings, name=name))
                    for lang, name in (("ro_RO", "Livrări"), ("en_US", "Deliveries"))
                },
                "eval_wait": 2500,
                "highlight": [".o_data_row td[name='available_state']"],
            },
            {
                "url": self._picking_url(self.picking_done),
                "name": "10_livrare_stare_colet.png",
                "wait": ".o_form_view div[name='delivery_state']",
                "highlight": ["div[name='delivery_state']"],
            },
        ]

    def _capture(self, lang):
        self.capture_screenshots(self._shots_config() + self._shots_flow(), lang=lang, hide_systray=True)

    def test_capture_fise(self):
        self._capture("ro_RO")

    def test_capture_usage(self):
        self._capture("en_US")

    def _gif_steps(self):
        return [
            {"goto": self._order_url(self.order), "wait": ".o_form_view button[name='postpone_delivery']"},
            {
                "caption": {
                    "ro_RO": "Comanda e confirmată, iar livrarea așteaptă plata",
                    "en_US": "The order is confirmed and the delivery waits for the payment",
                },
                "hold": 900,
            },
            {
                "click": "button[name='postpone_delivery']",
                "wait_after": "button[name='release_delivery']",
                "hold": 1500,
            },
            {
                "caption": {
                    "ro_RO": "Livrarea e amânată: transferul nu se poate valida",
                    "en_US": "The delivery is postponed: the transfer cannot be validated",
                },
                "hold": 1500,
            },
            {
                "caption": {
                    "ro_RO": "După plată, livrarea se eliberează",
                    "en_US": "After the payment, the delivery is released",
                }
            },
            {
                "click": "button[name='release_delivery']",
                "wait_after": "button[name='postpone_delivery']",
                "hold": 2000,
            },
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_gif(self):
        """GIF-ul demo: amânarea și eliberarea livrării din comandă, în RO și EN."""
        # banner.json e în engleză: slide-ul RO primește textele lui
        intro_ro = {
            "title": "Starea livrării",
            "summary": "Livrarea amânată până la plată și starea coletului la curier",
            "features": ["Amânare livrare până la plată", "Disponibilitate pe transfer", "Starea coletului"],
        }
        self.capture_gif(self._gif_steps(), name="demo.gif", intro=intro_ro)
        self.capture_gif(self._gif_steps(), name="demo.gif", lang="en_US")
