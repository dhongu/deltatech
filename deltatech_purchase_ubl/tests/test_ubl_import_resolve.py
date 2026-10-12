# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from base64 import b64encode

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .test_ubl_import import _xml_invoice


@tagged("post_install", "-at_install")
class TestUblImportResolve(TransactionCase):
    """Vendor/order resolution, product matching and unit handling."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.Wizard = cls.env["purchase.ubl.import.wizard"]
        cls.vendor = cls.env["res.partner"].create(
            {"name": "Resolve Vendor SRL", "is_company": True, "vat": "RO20000002", "supplier_rank": 1}
        )
        cls.unit = cls.env.ref("uom.product_uom_unit")
        cls.kg = cls.env.ref("uom.product_uom_kgm")
        cls.gram = cls.env.ref("uom.product_uom_gram")

    def _product(self, name, **vals):
        return self.env["product.product"].create(dict({"name": name, "is_storable": True}, **vals))

    def _order(self, products=(), **vals):
        return self.env["purchase.order"].create(
            dict(
                {
                    "partner_id": self.vendor.id,
                    "company_id": self.company.id,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": product.id,
                                "product_qty": 1.0,
                                "price_unit": 1.0,
                                "name": product.name,
                                "product_uom_id": product.uom_id.id,
                                "date_planned": "2025-01-01 00:00:00",
                            },
                        )
                        for product in products
                    ],
                },
                **vals,
            )
        )

    # ------------------------------------------------------------------
    # Vendor
    # ------------------------------------------------------------------
    def test_find_supplier_partner_by_vat_then_name(self):
        self.assertEqual(self.Wizard._find_supplier_partner("ro20000002", ""), self.vendor)
        # unknown VAT: falls back to the registration name
        self.assertEqual(self.Wizard._find_supplier_partner("RO99999999", "resolve vendor srl"), self.vendor)
        self.assertFalse(self.Wizard._find_supplier_partner("", ""))

    def test_find_supplier_partner_ignores_ro_prefix_and_spaces(self):
        Partner = self.env["res.partner"]
        with_prefix = Partner.create({"name": "VAT With Prefix SRL", "vat": "RO31000003", "supplier_rank": 1})
        without_prefix = Partner.create({"name": "VAT Without Prefix SRL", "vat": "32000004", "supplier_rank": 1})
        foreign = Partner.create({"name": "VAT Foreign GmbH", "vat": "DE123456789", "supplier_rank": 1})
        find = self.Wizard._find_supplier_partner

        self.assertEqual(find("31000003", ""), with_prefix)
        self.assertEqual(find("ro 31000003", ""), with_prefix)
        self.assertEqual(find("RO32000004", ""), without_prefix)
        # a longer or shorter number is another company
        self.assertFalse(find("RO3100000", ""))
        self.assertFalse(find("RO310000031", ""))
        # only the Romanian prefix is optional
        self.assertFalse(find("123456789", ""))
        self.assertEqual(find("de 123456789", ""), foreign)

    def test_vat_mismatch_warning_ignores_prefix(self):
        order = self._order()
        wizard = self.Wizard.create({"data_file": b64encode(_xml_invoice()), "order_id": order.id})
        _order, _partner, mismatch = wizard._resolve_order_and_partner({"supplier_vat": "20000002"})
        self.assertFalse(mismatch)
        _order, _partner, mismatch = wizard._resolve_order_and_partner({"supplier_vat": "RO 20000002"})
        self.assertFalse(mismatch)
        _order, _partner, mismatch = wizard._resolve_order_and_partner({"supplier_vat": "RO20000003"})
        self.assertTrue(mismatch)

    def test_supplier_without_vat_scheme_found_by_legal_entity_id(self):
        """A supplier not registered for VAT sends its CUI only in PartyLegalEntity/CompanyID."""
        xml = _xml_invoice(order_ref="", supplier_vat="20000002", supplier_name="Some Other Name")
        xml = xml.replace(b"<cac:PartyTaxScheme><cbc:CompanyID>20000002</cbc:CompanyID></cac:PartyTaxScheme>", b"")
        xml = xml.replace(
            b"<cac:PartyLegalEntity>", b"<cac:PartyLegalEntity><cbc:CompanyID>20000002</cbc:CompanyID>", 1
        )
        data = self.Wizard._parse_xml(xml)
        self.assertEqual(data["supplier_vat"], "20000002")
        self.assertEqual(self.Wizard._find_supplier_partner(data["supplier_vat"], data["supplier_name"]), self.vendor)

    def test_unknown_vendor_without_order_raises(self):
        xml = _xml_invoice(order_ref="", supplier_vat="RO30000003", supplier_name="Unknown Vendor SRL")
        wizard = self.Wizard.create({"data_file": b64encode(xml)})
        with self.assertRaises(UserError):
            wizard.action_import()

    # ------------------------------------------------------------------
    # Purchase order
    # ------------------------------------------------------------------
    def test_find_order_from_xml_variants(self):
        self.assertFalse(self.Wizard._find_order_from_xml(""))
        older = self._order(partner_ref="RES-REF-1")
        newer = self._order(partner_ref="RES-REF-1")
        cancelled = self._order(partner_ref="RES-REF-2")
        cancelled.button_cancel()

        # same reference on two orders: the newest one wins, also without a vendor
        self.assertEqual(self.Wizard._find_order_from_xml("RES-REF-1", self.vendor), newer)
        self.assertEqual(self.Wizard._find_order_from_xml("RES-REF-1"), newer)
        self.assertEqual(self.Wizard._find_order_from_xml(older.name), older)
        self.assertFalse(self.Wizard._find_order_from_xml("RES-REF-2"))
        self.assertFalse(self.Wizard._find_order_from_xml("RES-MISSING"))

    def test_resolve_order_from_active_id_context(self):
        order = self._order()
        xml = _xml_invoice(order_ref="", supplier_vat="", supplier_name="")
        wizard = self.Wizard.create({"data_file": b64encode(xml)})
        self.assertFalse(wizard.order_id)
        resolved, partner, vat_mismatch = wizard.with_context(
            active_model="purchase.order", active_id=order.id
        )._resolve_order_and_partner(wizard._parse_xml(xml))
        self.assertEqual(resolved, order)
        self.assertEqual(partner, self.vendor)
        self.assertFalse(vat_mismatch)

    # ------------------------------------------------------------------
    # Product matching
    # ------------------------------------------------------------------
    def test_match_product_global_paths(self):
        by_code = self._product("Resolve By Code")
        self.env["product.supplierinfo"].create(
            {"partner_id": self.vendor.id, "product_tmpl_id": by_code.product_tmpl_id.id, "product_code": "RV-01"}
        )
        by_vendor_name = self._product("Resolve Internal Name")
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.vendor.id,
                "product_tmpl_id": by_vendor_name.product_tmpl_id.id,
                "product_name": "Vendor Label 77",
            }
        )
        by_barcode = self._product("Resolve By Barcode", barcode="5940000000017")
        self._product("Resolve Twin")
        self._product("Resolve Twin")

        match = self.Wizard._match_product_detailed
        # unknown barcode falls through to the vendor code
        self.assertEqual(match(self.vendor, "RV-01", "", barcode="0000000000000"), (by_code, "code"))
        self.assertEqual(match(self.vendor, "", "Vendor Label 77"), (by_vendor_name, "name"))
        # a numeric supplier code that is in fact the EAN
        self.assertEqual(match(self.vendor, "5940000000017", ""), (by_barcode, "barcode"))
        # two products with the same name: the exact name match is ambiguous
        product, match_type = match(self.vendor, "", "Resolve Twin")
        self.assertEqual(product.name, "Resolve Twin")
        self.assertEqual(match_type, "name")
        empty, match_type = match(self.vendor, "", "Resolve Nothing Like This")
        self.assertFalse(empty)
        self.assertFalse(match_type)
        self.assertFalse(match(self.vendor, "", "")[1])

    def test_match_product_on_order_paths(self):
        by_barcode = self._product("Order Barcode", barcode="5940000000024")
        by_vendor_code = self._product("Order Vendor Code")
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.vendor.id,
                "product_tmpl_id": by_vendor_code.product_tmpl_id.id,
                "product_code": "OV-02",
            }
        )
        by_default_code = self._product("Order Default Code", default_code="OD-03")
        by_numeric_code = self._product("Order Numeric", barcode="5940000000031")
        by_name = self._product("Order Name Only")
        order = self._order([by_barcode, by_vendor_code, by_default_code, by_numeric_code, by_name])

        match = self.Wizard._match_product_on_order_detailed
        self.assertEqual(match(order, self.vendor, "", "", barcode="5940000000024"), (by_barcode, "barcode"))
        self.assertEqual(match(order, self.vendor, "OV-02", ""), (by_vendor_code, "code"))
        self.assertEqual(match(order, self.vendor, "OD-03", ""), (by_default_code, "code"))
        self.assertEqual(match(order, self.vendor, "5940000000031", ""), (by_numeric_code, "barcode"))
        self.assertEqual(match(order, self.vendor, "", " Order Name Only "), (by_name, "name"))
        self.assertFalse(match(order, self.vendor, "NOPE", "Nope")[0])
        self.assertFalse(match(self.env["purchase.order"], self.vendor, "OD-03", "")[0])

    # ------------------------------------------------------------------
    # Units and vendor prices
    # ------------------------------------------------------------------
    def test_convert_source_line_edge_cases(self):
        convert = self.Wizard._convert_source_line
        # incompatible unit without a warning collector: kept as is
        self.assertEqual(convert({"qty": 3.0, "price": 2.0, "unit_code": "KGM"}, self.unit), (3.0, 2.0))
        # zero quantity/price are left untouched by the conversion
        self.assertEqual(convert({"qty": 0.0, "price": 0.0, "unit_code": "GRM"}, self.kg), (0.0, 0.0))
        self.assertEqual(convert({"qty": 1000.0, "price": 0.01, "unit_code": "GRM"}, self.kg), (1.0, 10.0))

    def test_update_supplier_price_without_or_with_incompatible_unit(self):
        product = self._product("Resolve Price Product")
        self.Wizard._update_supplier_price(self.vendor, product, "RP-1", 7.0, "RON", uom=False)
        sinfo = product.seller_ids
        self.assertEqual(sinfo.price, 7.0)
        self.assertEqual(sinfo.product_uom_id, self.unit)
        # incompatible source unit: price kept, unit of the pricelist row unchanged
        self.Wizard._update_supplier_price(self.vendor, product, "RP-1", 8.0, "RON", uom=self.kg)
        self.assertEqual(sinfo.price, 8.0)
        self.assertEqual(sinfo.product_uom_id, self.unit)

    def test_foreign_currency_price_update(self):
        eur = self.env.ref("base.EUR")
        eur.active = True
        product = self._product("Resolve EUR Product", default_code="REUR-1")
        xml = _xml_invoice(
            invoice_id="",
            order_ref="",
            currency="EUR",
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=[{"code": "REUR-1", "name": product.name, "qty": "1", "price": "4.5", "line_total": "4.5"}],
        )
        wizard = self.Wizard.create({"data_file": b64encode(xml), "create_missing_products": False})
        wizard.action_import()
        self.assertEqual(product.seller_ids.currency_id, eur)
        self.assertEqual(product.seller_ids.price, 4.5)

    def test_new_order_line_with_incompatible_unit_uses_product_unit(self):
        product = self._product("Resolve Pieces", default_code="RPCS-1")
        order = self._order()
        xml = _xml_invoice(
            invoice_id="",
            order_ref=order.name,
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=[{"code": "RPCS-1", "name": product.name, "qty": "2", "price": "3", "unit_code": "KGM"}],
        )
        wizard = self.Wizard.with_context(active_model="purchase.order", active_id=order.id).create(
            {"data_file": b64encode(xml), "update_prices": False, "create_missing_products": False}
        )
        wizard.action_import()
        self.assertEqual(order.order_line.product_id, product)
        self.assertEqual(order.order_line.product_uom_id, self.unit)
        self.assertEqual(order.order_line.product_qty, 2.0)
        self.assertIn("not compatible", wizard.log)

    def test_receipt_validation_skipped_without_order(self):
        self._product("Resolve No Order", default_code="RNO-1")
        xml = _xml_invoice(
            invoice_id="",
            order_ref="",
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=[{"code": "RNO-1", "name": "Resolve No Order", "qty": "1", "price": "1"}],
        )
        wizard = self.Wizard.create(
            {"data_file": b64encode(xml), "validate_receipt": True, "create_missing_products": False}
        )
        wizard.action_import()
        self.assertIn("Receipt validation skipped", wizard.log)
