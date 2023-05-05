# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

import psycopg2.extras

from odoo import fields, models

_logger = logging.getLogger(__name__)


class VendorProduct(models.Model):
    _name = "vendor.product"
    _description = "Vendor Product"

    name = fields.Char(string="Product Name", required=True, index=True)
    code = fields.Char(string="Product Code", required=True, index=True)
    barcode = fields.Char()

    list_price = fields.Float(string="Sale Price", required=True, digits="Product Price")
    purchase_price = fields.Float(string="Purchase Price", digits="Product Price")
    supplier_id = fields.Many2one("res.partner", string="Supplier", index=True)
    product_id = fields.Many2one("product.product", string="Product", ondelete="set null")

    supplierinfo_id = fields.Many2one("product.supplierinfo", string="Supplier Info", ondelete="set null")

    _sql_constraints = [("code_supplier_uniq", "unique (code,supplier_id)", "The code must be unique per supplier!")]

    def search_product(self):
        query = """
        UPDATE vendor_product vp
            SET product_id = pp.id
                FROM product_product pp join product_supplierinfo psi on pp.id = psi.product_id
                WHERE vp.code = psi.product_code
                    AND vp.supplier_id = psi.name
                    AND vp.product_id is null
                    AND vp.id in %s
        """
        self.env.cr.execute(query, (tuple(self.ids),))

        query = """
         UPDATE vendor_product vp
            SET product_id = pp.id
              FROM product_product pp join product_supplierinfo psi on pp.product_tmpl_id = psi.product_tmpl_id
                WHERE vp.code = psi.product_code
                    AND vp.supplier_id = psi.name
                    AND vp.product_id is null
                    AND vp.id in %s
        """
        self.env.cr.execute(query, (tuple(self.ids),))

    def update_product_supplierinfo(self):
        """Update price"""
        query = """
        UPDATE product_supplierinfo psi
            SET price = vp.purchase_price
                FROM vendor_product vp
                JOIN product_product pp on pp.id = vp.product_id
                WHERE  psi.product_tmpl_id = pp.product_tmpl_id
                    AND vp.supplier_id = psi.name
                    AND vp.purchase_price > 0
                    AND vp.id in %s
        """
        self.env.cr.execute(query, (tuple(self.ids),))

    def create_product(self):
        self.search_product()
        products = self.env["product.product"]
        for vendor_product in self:

            vendor_info = self.env["vendor.info"].search([("supplier_id", "=", vendor_product.supplier_id.id)], limit=1)
            if not vendor_info:
                vendor_info = self.env["vendor.info"].create(
                    {
                        "supplier_id": vendor_product.supplier_id.id,
                        "name": vendor_product.supplier_id.name,
                    }
                )

            seller_values = {
                "name": vendor_product.supplier_id.id,
                "product_code": vendor_product.code,
                "product_name": vendor_product.name,
                "delay": vendor_info.purchase_delay,
                "price": vendor_product.purchase_price,
                "currency_id": vendor_info.currency_id.id,
            }

            values = {
                "name": vendor_product.name,
                "barcode": vendor_product.barcode,
                "list_price": vendor_product.list_price,
                "standard_price": vendor_product.purchase_price,
                "seller_ids": [(0, 0, seller_values)],
            }
            if vendor_info.category_id:
                values["categ_id"] = vendor_info.category_id.id

            if vendor_product.product_id:
                products |= vendor_product.product_id
                vendors = vendor_product.product_id.seller_ids.filtered(lambda s: s.name == vendor_product.supplier_id)
                if not vendors:
                    vendor_product.product_id.write({"seller_ids": [(0, 0, seller_values)]})
                continue

            if vendor_info.type_code == "sequence":
                values["default_code"] = vendor_info.sequence_id.next_by_id()
            elif vendor_info.type_code == "code":
                values["default_code"] = vendor_product.code

            product = self.env["product.product"].create(values)
            vendor_product.write({"product_id": product.id})
            products |= product

        action = self.env["ir.actions.actions"]._for_xml_id("purchase.product_product_action")
        action["domain"] = [("id", "in", products.ids)]
        return action

    def create_staging_table(self, fields_name) -> None:
        self.env.cr.execute(
            """
            DROP TABLE IF EXISTS staging_vendor_product;
            CREATE UNLOGGED TABLE staging_vendor_product
            AS SELECT %s FROM vendor_product WITH NO DATA;
        """,
            (", ".join(fields_name),),
        )

    def _load_data_in_table(self, values, fields_list):
        query = " INSERT INTO  vendor_product ( %s )" % ",".join(fields_list)
        query += " VALUES %s "
        if "code" in fields_list:
            query += " ON CONFLICT (code, supplier_id) DO UPDATE SET "
            query += ",".join([f + "=EXCLUDED." + f for f in fields_list if f != "code"])

        psycopg2.extras.execute_values(self.env.cr, query, values, page_size=1000)
        _logger.info("Inserting %s records into vendor_product" % len(values))

    def _load_records(self, data_list, update=False):
        supplier_id = self.env.context.get("default_supplier_id", False)

        fields_name = list(data_list[0]["values"].keys())
        codes = []
        if "code" in fields_name:
            codes = list(map(lambda l: l["values"]["code"], data_list))

        if codes:
            values = list(map(lambda l: tuple(l["values"].values()), data_list))
            fields_name = list(data_list[0]["values"].keys())

            if supplier_id and "supplier_id" not in fields_name:
                fields_name.append("supplier_id")
                values = list(map(lambda l: tuple(l["values"].values()) + (supplier_id,), data_list))

            # self.create_staging_table(fields_name)

            params = {
                "fields": ", ".join(fields_name),
                "values": values,
            }
            self._load_data_in_table(values, params["fields"])

            if supplier_id:
                self.env.cr.execute(
                    "SELECT id FROM vendor_product WHERE code IN %s AND supplier_id = %s", (tuple(codes), supplier_id)
                )
            else:
                self.env.cr.execute("SELECT id FROM vendor_product WHERE code IN %s", (tuple(codes),))
            ids = [t[0] for t in self.env.cr.fetchall()]

            return self.browse(ids)

        # for data in data_list:
        #     code = data["values"].get("code", False)
        #     if "supplier_id" in data["values"]:
        #         supplier_id = data["values"]["supplier_id"]
        #     if code and supplier_id:
        #         domain = [("code", "=", code), ("supplier_id", "=", supplier_id)]
        #         record = self.env["vendor.product"].search(domain, limit=1)
        #         if record:
        #             data["values"]["id"] = record.id
        #         else:
        #             data["values"]["id"] = False
        # return
        return super(VendorProduct, self.sudo())._load_records(data_list, update)
