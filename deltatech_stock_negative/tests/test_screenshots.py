# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Interzicerea stocului negativ la validarea
# transferurilor" — generate în timpul testelor, în limba RO, pe compania
# „Demo Stoc SRL" în RON.
#
# Seedează o politică activă pe companie, o locație scutită (Tranzit), o locație
# fără verificarea seriei (Raft Serii), un transfer care se blochează la validare
# (două rânduri de câte 1 buc pe un stoc de 1 buc) și o poziție negativă de
# corectat prin inventar.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_stock_negative,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestStockNegativeScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_stock_negative"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Stoc SRL")
        company = cls.env.company
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})

        # drepturi de stoc + grupurile care fac vizibile locațiile, loturile,
        # pachetele, proprietarii și unitățile de măsură în capturi
        groups = [
            "stock.group_stock_manager",
            "stock.group_stock_multi_locations",
            "stock.group_production_lot",
            "stock.group_tracking_lot",
            "stock.group_tracking_owner",
            "uom.group_uom",
        ]
        for xmlid in groups:
            group = env.ref(xmlid)
            env.user.group_ids = [Command.link(group.id)]
            admin.group_ids = [Command.link(group.id)]
        # bifele din Setări citesc grupurile implicate pe utilizatorul intern, nu pe
        # admin: le activăm prin configurare, ca în captură să apară bifate
        env["res.config.settings"].create(
            {
                "group_stock_multi_locations": True,
                "group_stock_production_lot": True,
                "group_stock_tracking_lot": True,
                "group_stock_tracking_owner": True,
                "group_uom": True,
                "no_negative_stock": True,
            }
        ).execute()
        env.flush_all()

        cls.warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        cls.warehouse.write({"name": "Depozit central", "code": "WH"})
        cls.stock = cls.warehouse.lot_stock_id
        Location = env["stock.location"]
        cls.raft_a = Location.create({"name": "Raft A", "usage": "internal", "location_id": cls.stock.id})
        cls.tranzit = Location.create(
            {"name": "Tranzit", "usage": "internal", "location_id": cls.stock.id, "allow_negative_stock": True}
        )
        # destinația transferurilor validate, în afara pozițiilor arătate la pasul 5
        cls.rampa = Location.create({"name": "Rampă livrare", "usage": "internal", "location_id": cls.stock.id})
        cls.raft_serii = Location.create(
            {"name": "Raft Serii", "usage": "internal", "location_id": cls.stock.id, "check_serial_no": False}
        )

        Product = env["product.product"]
        cls.cablu = Product.create({"name": "Cablu UTP Cat6", "is_storable": True})
        cls.suruburi = Product.create({"name": "Șuruburi M6", "is_storable": True})
        cls.vopsea = Product.create({"name": "Vopsea lavabilă 10L", "is_storable": True, "tracking": "lot"})
        cls.router = Product.create({"name": "Router WiFi 6", "is_storable": True, "tracking": "serial"})
        cls.banda = Product.create({"name": "Bandă adezivă 50 mm", "is_storable": True})

        Lot = env["stock.lot"]
        lot_1, lot_2 = Lot.create(
            [
                {"name": "L-2026-01", "product_id": cls.vopsea.id, "company_id": company.id},
                {"name": "L-2026-02", "product_id": cls.vopsea.id, "company_id": company.id},
            ]
        )
        sn_1, sn_2 = Lot.create(
            [
                {"name": "SN-1001", "product_id": cls.router.id, "company_id": company.id},
                {"name": "SN-1002", "product_id": cls.router.id, "company_id": company.id},
            ]
        )
        cls.package = env["stock.package"].create({"name": "PACK-0001"})
        cls.owner = env["res.partner"].create({"name": "Client Custodie SRL", "country_id": env.ref("base.ro").id})

        Quant = env["stock.quant"]
        Quant._update_available_quantity(cls.cablu, cls.raft_a, 1.0)
        Quant._update_available_quantity(cls.cablu, cls.stock, 1.0, package_id=cls.package)
        Quant._update_available_quantity(cls.cablu, cls.stock, 3.0, owner_id=cls.owner)
        Quant._update_available_quantity(cls.suruburi, cls.stock, 12.0)
        Quant._update_available_quantity(cls.vopsea, cls.stock, 1.0, lot_id=lot_1)
        Quant._update_available_quantity(cls.vopsea, cls.stock, 1.0, lot_id=lot_2)
        Quant._update_available_quantity(cls.router, cls.raft_serii, 1.0, lot_id=sn_1)
        Quant._update_available_quantity(cls.router, cls.raft_serii, 1.0, lot_id=sn_2)
        Quant._update_available_quantity(cls.cablu, cls.tranzit, 1.0)
        # poziție negativă rămasă din perioada fără politică, de corectat prin inventar
        Quant._update_available_quantity(cls.banda, cls.stock, -5.0)

        internal = cls.warehouse.int_type_id
        # tipul de operație e creat înaintea limbii RO, deci are numele în engleză
        internal.name = "Transferuri interne"

        # 3–4. transfer intern de 2 buc din Raft A, unde e 1 buc: operatorul a selectat
        # în Operații detaliate două linii de câte 1 buc. Se blochează la Validează.
        cls.picking_blocked = cls._picking(internal, cls.raft_a, cls.stock, [(cls.cablu, 2.0)], validate=False)
        move = cls.picking_blocked.move_ids
        move.move_line_ids.unlink()
        for _i in range(2):
            env["stock.move.line"].create({**move._prepare_move_line_vals(), "quantity": 1.0})
        move.picked = True

        # 6. din Tranzit (stoc negativ permis): 2 buc pe un stoc de 1 buc se validează
        picking_tranzit = cls._picking(internal, cls.tranzit, cls.rampa, [(cls.cablu, 2.0)])
        picking_tranzit.button_validate()

        # 7. Raft Serii (Check Serial No. debifat): ambele serii, validat
        cls.picking_serial = cls._picking(internal, cls.raft_serii, cls.rampa, [(cls.router, 2.0)], validate=False)
        move = cls.picking_serial.move_ids
        move.move_line_ids.unlink()
        for lot in sn_1 | sn_2:
            env["stock.move.line"].create({**move._prepare_move_line_vals(), "quantity": 1.0, "lot_id": lot.id})
        move.picked = True
        cls.picking_serial.button_validate()

        # 8. inventarierea fizică a poziției negative: numărat 0, încă neaplicat
        cls.quant_negative = Quant.search([("product_id", "=", cls.banda.id), ("location_id", "=", cls.stock.id)])
        cls.quant_negative.inventory_quantity = 0.0
        cls.quant_negative.inventory_quantity_set = True

        Action = env["ir.actions.act_window"]
        quant_list = env.ref("stock.view_stock_quant_tree")
        cls.action_positions = Action.create(
            {
                "name": "Stock by Location",
                "res_model": "stock.quant",
                "view_mode": "list",
                "view_id": quant_list.id,
                "domain": [
                    ("product_id", "in", (cls.cablu | cls.vopsea).ids),
                    ("location_id", "in", (cls.raft_a | cls.stock).ids),
                ],
            }
        )
        cls.action_tranzit = Action.create(
            {
                "name": "Stock by Location",
                "res_model": "stock.quant",
                "view_mode": "list",
                "view_id": quant_list.id,
                "domain": [("location_id", "=", cls.tranzit.id)],
            }
        )
        cls.action_inventory = Action.create(
            {
                "name": "Inventariere fizică",
                "res_model": "stock.quant",
                "view_mode": "list",
                "view_id": env.ref("stock.view_stock_quant_tree_inventory_editable").id,
                "domain": [("id", "=", cls.quant_negative.id)],
                "context": "{'inventory_mode': True}",
            }
        )
        cls.settings_action = env.ref("stock.action_stock_config_settings")
        env.flush_all()

    @classmethod
    def _picking(cls, picking_type, source, dest, lines, validate=True):
        """Transfer confirmat, cu cantitățile selectate (picked), gata de Validează."""
        picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": source.id,
                "location_dest_id": dest.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "uom_id": product.uom_id.id,
                            "product_uom_qty": qty,
                            "location_id": source.id,
                            "location_dest_id": dest.id,
                        }
                    )
                    for product, qty in lines
                ],
            }
        )
        picking.action_confirm()
        if validate:
            for move in picking.move_ids:
                move.quantity = move.product_uom_qty
                move.picked = True
        return picking

    def test_capture_fise(self):
        scroll_setting = (
            "document.querySelector(\"[name='no_negative_stock']\")"
            ".closest('.o_setting_box, .o_setting_container, .row').scrollIntoView({block: 'center'})"
        )
        self.capture_screenshots(
            [
                # 1. bifa „Fără stoc negativ", în Setări → Trasabilitate
                {
                    "url": f"action={self.settings_action.id}",
                    "name": "01_setari_fara_stoc_negativ.png",
                    "wait": "[name='no_negative_stock']",
                    "timeout": 40000,
                    "eval": scroll_setting,
                    "settle": 3000,
                    "highlight": ["div[name='no_negative_stock']"],
                },
                # 2. cele două câmpuri ale modulului pe formularul locației
                {
                    "url": f"id={self.tranzit.id}&model=stock.location&view_type=form",
                    "name": "02_locatie_optiuni.png",
                    "wait": ".o_form_view",
                    "settle": 2000,
                    "highlight": ["div[name='allow_negative_stock']", "div[name='check_serial_no']"],
                },
                # 3. Operații detaliate: două linii de câte 1 buc din Raft A
                {
                    "url": f"id={self.picking_blocked.id}&model=stock.picking&view_type=form",
                    "name": "03_transfer_doua_linii.png",
                    "wait": ".o_form_view",
                    "click_btn": "button[name='action_show_details']",
                    "wait_after": ".modal .o_list_view",
                    "settle": 2500,
                },
                # 4. dialogul de blocare la Validează
                {
                    "url": f"id={self.picking_blocked.id}&model=stock.picking&view_type=form",
                    "name": "04_eroare_stoc_negativ.png",
                    "wait": ".o_form_view",
                    "click_btn": "button[name='button_validate']",
                    "wait_after": ".modal .modal-body",
                    "settle": 3000,
                    "highlight": [".modal .modal-content"],
                },
                # 5. pozițiile de stoc pe locație, lot, pachet, proprietar
                {
                    "url": f"action={self.action_positions.id}",
                    "name": "05_pozitii_stoc.png",
                    "wait": ".o_list_view",
                    "settle": 2500,
                },
                # 6. poziția negativă pe locația scutită
                {
                    "url": f"action={self.action_tranzit.id}",
                    "name": "06_locatie_stoc_negativ_permis.png",
                    "wait": ".o_list_view",
                    "settle": 2500,
                },
                # 7. transferul validat pe două serii, pe Raft Serii
                {
                    "url": f"id={self.picking_serial.id}&model=stock.picking&view_type=form",
                    "name": "07_serie_check_debifat.png",
                    "wait": ".o_form_view",
                    "click_btn": "button[name='action_show_details']",
                    "wait_after": ".modal .o_list_view",
                    "settle": 2500,
                },
                # 8. inventarierea fizică a poziției negative, înainte de Aplică
                {
                    "url": f"action={self.action_inventory.id}",
                    "name": "08_inventar_corectie_negativ.png",
                    "wait": ".o_list_view",
                    "settle": 2500,
                },
            ],
            hide_systray=True,
        )
