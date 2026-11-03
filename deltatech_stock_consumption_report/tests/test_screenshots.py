# Capturi de ecran pentru fișa „Raportul lunar al bonurilor de consum" — generate în teste, în RO
# (fișa consultant) și în EN (readme/USAGE.md), pe localizarea română: locația de tip Consum vine
# din `l10n_ro_stock_account`, fără ea testul se sare.
#
# Seedează două magazine (Magazin Nord, Magazin Sud), fiecare cu tipul lui de operațiune de consum,
# două destinații de consum (Consum propriu, Investiții), două consumabile și o marfă (cimentul).
# Fluxul corect pentru marfa folosită intern: transfer la cost din stoc în gestiunea de materiale a
# magazinului (Dr 3028 = Cr 371, categoria permite schimbarea contului de stoc), apoi bonul de consum
# din materiale (Dr 6028 = Cr 3028). La Magazin Sud, un bon-anomalie dă cimentul direct din stoc pe
# consum (Dr 607 = Cr 371): fișa îl folosește ca exemplu de ce trebuie găsit în raport, prin coloana
# „livrat clienților" (o livrare către client pentru ciment).
# Planul de conturi RO (`setup_country("ro")`) și valorizarea în timp real fac ca bonul să aibă și
# nota de consum.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> --without-demo=all \
#       -i deltatech_stock_consumption_report,deltatech_doc_screenshots,l10n_ro_stock_account \
#       --test-tags=fise_screenshots --stop-after-init

import base64
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import (
        ScreenshotCase,
    )
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestConsumptionReportScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_stock_consumption_report"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        if "consume" not in cls.env["stock.location"]._get_consumption_usages():
            raise unittest.SkipTest("l10n_ro_stock_account neinstalat")
        cls.company = cls.prepare_ro_company(name="RO Company")
        admin = cls.env.ref("base.user_admin")
        admin.write(
            {
                "company_ids": [Command.link(cls.company.id)],
                "company_id": cls.company.id,
            }
        )
        admin.group_ids = [Command.link(cls.env.ref("stock.group_stock_manager").id)]
        cls.company.account_stock_journal_id = cls.env["account.journal"].create(
            {
                "name": "Stocuri",
                "code": "STK",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls.consume_location = cls.env["stock.location"].create(
            {"name": "Consum", "usage": "consume", "company_id": cls.company.id}
        )
        cls.stores = cls.env["stock.warehouse"]
        cls.consume_types = cls.env["stock.picking.type"]
        for name, code in (("Magazin Nord", "NRD"), ("Magazin Sud", "SUD")):
            warehouse = cls.env["stock.warehouse"].create({"name": name, "code": code, "company_id": cls.company.id})
            cls.stores |= warehouse
            cls.consume_types |= cls.env["stock.picking.type"].create(
                {
                    "name": "Consum",
                    "code": "internal",
                    "sequence_code": "CNS",
                    "warehouse_id": warehouse.id,
                    "company_id": cls.company.id,
                    "default_location_src_id": warehouse.lot_stock_id.id,
                    "default_location_dest_id": cls.consume_location.id,
                }
            )
        category = cls.env["product.category"]
        consumables = category.create(cls._category_vals("Consumabile", stock="3028", expense="6028"))
        # marfă (371 / 607); contul de stoc se schimbă după gestiune, ca marfa trecută în
        # materiale să ajungă pe 3028
        goods = category.create(cls._category_vals("Mărfuri", stock="371", expense="607"))
        goods.l10n_ro_stock_account_change = True
        product = cls.env["product.product"]
        cls.gloves = product.create(
            {
                "name": "Mănuși de protecție latex",
                "default_code": "MAN-09",
                "is_storable": True,
                "standard_price": 7.70,
                "categ_id": consumables.id,
            }
        )
        cls.detergent = product.create(
            {
                "name": "Detergent vase 1 l",
                "default_code": "DET-01",
                "is_storable": True,
                "standard_price": 9.25,
                "categ_id": consumables.id,
            }
        )
        cls.cement = product.create(
            {
                "name": "Ciment 20 kg",
                "default_code": "CIM-20",
                "is_storable": True,
                "standard_price": 12.64,
                "categ_id": goods.id,
            }
        )
        for warehouse in cls.stores:
            for prod in (cls.gloves, cls.detergent, cls.cement):
                cls.env["stock.quant"]._update_available_quantity(prod, warehouse.lot_stock_id, 100.0)

        purpose = cls.env["stock.consumption.purpose"]
        own_use = purpose.create({"name": "Consum propriu", "sequence": 1, "company_id": cls.company.id})
        investments = purpose.create({"name": "Investiții", "sequence": 2, "company_id": cls.company.id})
        north, south = cls.stores
        north_type, south_type = cls.consume_types
        materials = cls.env["stock.location"].create(
            {
                "name": "Materiale uz intern",
                "usage": "internal",
                "location_id": north.view_location_id.id,
                "company_id": cls.company.id,
                "l10n_ro_property_stock_valuation_account_id": cls._account("3028").id,
                "l10n_ro_property_account_expense_location_id": cls._account("6028").id,
            }
        )
        cls.voucher = cls._consume(north, north_type, [(cls.gloves, 5), (cls.detergent, 2)], own_use)
        cls.transfer = cls._validate(north.int_type_id, materials, [(cls.cement, 10)])
        cls.investment = cls._consume(north, north_type, [(cls.cement, 10)], investments, source=materials)
        cls._consume(south, south_type, [(cls.gloves, 2), (cls.detergent, 1)], own_use)
        cls.anomaly = cls._consume(south, south_type, [(cls.cement, 4)], own_use)
        cls._deliver(north, cls.cement, 30)

        cls.xlsx = {lang: cls._export(lang) for lang in ("ro_RO", "en_US")}
        cls.voucher_entry = cls.env["account.move"].search([("stock_move_ids", "in", cls.voucher.move_ids.ids)])
        cls.transfer_entry = cls.env["account.move"].search([("stock_move_ids", "in", cls.transfer.move_ids.ids)])
        cls.action = cls.env.ref("deltatech_stock_consumption_report.action_stock_consumption_report_wizard")
        cls.purpose_action = cls.env.ref("deltatech_stock_consumption_report.action_stock_consumption_purpose")

    @classmethod
    def _export(cls, lang):
        wizard = (
            cls.env["stock.consumption.report.wizard"].with_context(lang=lang).create({"company_id": cls.company.id})
        )
        wizard.action_export_xlsx()
        return base64.b64decode(wizard.file_data)

    @classmethod
    def _account(cls, prefix):
        return cls.env["account.account"].search(
            [("code", "=like", f"{prefix}%"), ("company_ids", "in", cls.company.ids)],
            limit=1,
        )

    @classmethod
    def _category_vals(cls, name, stock, expense):
        return {
            "name": name,
            "property_valuation": "real_time",
            "property_cost_method": "average",
            "property_stock_valuation_account_id": cls._account(stock).id,
            "property_account_expense_categ_id": cls._account(expense).id,
        }

    @classmethod
    def _validate(cls, picking_type, location_dest, lines, partner=None, purpose=None, source=None):
        source = source or picking_type.default_location_src_id
        picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "partner_id": partner and partner.id,
                "consumption_purpose_id": purpose and purpose.id,
                "location_id": source.id,
                "location_dest_id": location_dest.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": prod.id,
                            "product_uom_qty": qty,
                            "quantity": qty,
                            "location_id": source.id,
                            "location_dest_id": location_dest.id,
                        }
                    )
                    for prod, qty in lines
                ],
            }
        )
        picking.action_confirm()
        picking.move_ids.picked = True
        picking.button_validate()
        return picking

    @classmethod
    def _consume(cls, warehouse, picking_type, lines, purpose, source=None):
        return cls._validate(picking_type, cls.consume_location, lines, purpose=purpose, source=source)

    @classmethod
    def _deliver(cls, warehouse, prod, qty):
        customer = cls.env["res.partner"].create({"name": "Client Exemplu"})
        location = cls.env.ref("stock.stock_location_customers")
        return cls._validate(warehouse.out_type_id, location, [(prod, qty)], partner=customer)

    def _shots(self, lang):
        xlsx = self.xlsx[lang]
        titles = {
            "ro_RO": ("Centralizat", "Detaliat"),
            "en_US": ("Summary", "Detail"),
        }[lang]
        return [
            {
                "url": f"action={self.purpose_action.id}",
                "name": "01_destinatii_consum.png",
                "wait": ".o_list_view",
                "settle": 1500,
            },
            {
                "url": f"id={self.voucher.id}&model=stock.picking&view_type=form",
                "name": "02_bon_consum.png",
                "wait": ".o_form_view",
                "highlight": [
                    "div[name='picking_type_id']",
                    "div[name='consumption_purpose_id']",
                ],
                "settle": 2000,
            },
            self.account_move_shot(self.voucher_entry[:1], "03_nota_consum.png"),
            self.account_move_shot(self.transfer_entry[:1], "04_transfer_marfa.png"),
            {
                "url": f"action={self.action.id}",
                "name": "05_wizard_raport.png",
                "wait": ".modal-content",
                "highlight": [
                    "div[name='date_from']",
                    "div[name='picking_type_ids']",
                    "button[name='action_view']",
                ],
                "settle": 1500,
            },
            {
                "url": f"action={self.action.id}",
                "name": "06_pivot_consumuri.png",
                "wait": ".modal-content",
                "click_btn": "button[name='action_view']",
                "wait_after": ".o_pivot",
                "settle": 2000,
            },
            # foaia centralizată randată ca tabel: pagina tipărită taie ultima coloană
            {
                "html": self.xlsx_to_html(xlsx, sheet=0, title=titles[0], lang=lang),
                "name": "07_xlsx_centralizat.png",
                "full": True,
            },
            self.xlsx_shot(xlsx, "08_xlsx_detaliat.png", sheet=1, title=titles[1], lang=lang),
            self.account_move_shot(self.anomaly.move_ids.account_move_id[:1], "09_nota_anomalie.png"),
        ]

    def test_capture_fise(self):
        self.assertTrue(self.voucher_entry, "bonul de consum nu a generat notă contabilă")
        self.assertTrue(self.transfer_entry, "transferul în materiale nu a generat notă contabilă")
        for picking, debit, credit in ((self.investment, "6028", "3028"), (self.anomaly, "607", "371")):
            lines = picking.move_ids.account_move_id.line_ids
            self.assertTrue(lines.filtered("debit").account_id.code.startswith(debit))
            self.assertTrue(lines.filtered("credit").account_id.code.startswith(credit))
        self.capture_screenshots(self._shots("ro_RO"))

    def test_capture_usage(self):
        self.capture_screenshots(self._shots("en_US"), lang="en_US")
