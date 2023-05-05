# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import logging
import threading

import psycopg2.extras
import requests

from odoo import fields, models
from odoo.tools import image

_logger = logging.getLogger(__name__)


class VendorProduct(models.Model):
    _name = "vendor.product"
    _description = "Vendor Product"

    name = fields.Char(string="Product Name", required=True, index=True)
    code = fields.Char(string="Product Code", required=True, index=True)
    barcode = fields.Char(index=True)

    list_price = fields.Float(string="Sale Price", required=True, digits="Product Price")
    purchase_price = fields.Float(string="Purchase Price", digits="Product Price")
    supplier_id = fields.Many2one("res.partner", string="Supplier", index=True)
    vendor_info_id = fields.Many2one("vendor.info", string="Vendor Info", ondelete="cascade")

    product_id = fields.Many2one("product.product", string="Product", ondelete="set null")
    product_tmpl_id = fields.Many2one(
        "product.template", string="Product Template", related="product_id.product_tmpl_id"
    )
    url_image = fields.Char(string="Image URL")
    qty_available = fields.Float("Quantity Available", digits="Product Unit of Measure")

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
            SET price = vp.purchase_price,
                qty_available = vp.qty_available
                FROM vendor_product vp
                JOIN product_product pp on pp.id = vp.product_id
                WHERE  psi.product_tmpl_id = pp.product_tmpl_id
                    AND vp.supplier_id = psi.name
                    AND vp.purchase_price > 0
                    AND vp.id in %s
        """
        self.env.cr.execute(query, (tuple(self.ids),))

    def update_list_price(self):
        """Update price list"""
        query = """
        UPDATE product_template pt
            SET list_price =
            CASE vi.price_base
                WHEN 'list_price'
                  THEN
                    vp.list_price - (vp.list_price * (vi.price_discount / 100)) + price_surcharge
                WHEN 'purchase_price'
                 THEN
                  vp.purchase_price - (vp.purchase_price * (vi.price_discount / 100)) + price_surcharge
            END
                FROM vendor_product vp
                JOIN vendor_info vi on vi.supplier_id = vp.supplier_id
                JOIN product_product pp on pp.id = vp.product_id
                WHERE   pp.product_tmpl_id = pt.id AND vp.id in %s
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
                "currency_id": vendor_info.currency_id.id or self.env.company.currency_id.id,
                "qty_available": vendor_product.qty_available,
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

            product = vendor_product.product_id
            if product:
                vendors = product.seller_ids.filtered(lambda s: s.name == vendor_product.supplier_id)
                if not vendors:
                    product.write({"seller_ids": [(0, 0, seller_values)]})
            else:
                if vendor_info.type_code == "sequence":
                    values["default_code"] = vendor_info.sequence_id.next_by_id()
                elif vendor_info.type_code == "code":
                    values["default_code"] = vendor_product.code

                product = self.env["product.product"].create(values)
                vendor_product.write({"product_id": product.id})

            if vendor_product.url_image:
                vendor_product._load_image_thread(product.id, vendor_product.url_image)

            products |= product

        action = self.env["ir.actions.actions"]._for_xml_id("purchase.product_product_action")
        action["domain"] = [("id", "in", products.ids)]
        return action

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

    def get_session(self):
        return requests.Session()

    def load_image_from_url(self, url):
        try:
            session = self.get_session()
            data = base64.b64encode(session.get(url.strip()).content)  # .replace(b'\n', b'')
            image.base64_to_image(data)
        except Exception:
            data = False
        return data

    def _load_image_thread(self, product_id, url_image):
        threaded_calculation = threading.Thread(target=self._load_image, args=(product_id, url_image))
        threaded_calculation.start()
        return {"type": "ir.actions.act_window_close"}

    def _load_image(self, product_id, url_image):
        new_cr = self.pool.cursor()
        self = self.with_env(self.env(cr=new_cr))
        image_1920 = self.load_image_from_url(url_image)
        if image_1920:
            product = self.env["product.product"].browse(product_id)
            product = product.with_context(bin_size=False)
            product.write({"image_1920": image_1920})
            product._compute_can_image_1024_be_zoomed()

        new_cr.commit()
        new_cr.close()
        return {}
