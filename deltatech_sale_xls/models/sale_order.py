# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def show_order_lines(self):
        """Override to show order lines in the XLS report."""
        self.ensure_one()

        tree_view_id = self.env.ref("deltatech_sale_xls.sale_order_line_tree").id
        return {
            "type": "ir.actions.act_window",
            "name": "Sale Order Lines",
            "res_model": "sale.order.line",
            "view_mode": "list,form",
            "views": [(tree_view_id, "list")],
            "domain": [("order_id", "=", self.id)],
            "context": {"default_order_id": self.id, "create": True, "edit": True},
        }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _parse_import_data(self, data, import_fields, options):
        return super()._parse_import_data(data, import_fields, options)

    # def _load_records(self, data_list, update=False):
    #     order = self.env["purchase.order"]
    #     order_id = self.env.context.get("default_order_id", False) or self.env.context.get("active_id", False)
    #     if order_id:
    #         order = self.env["purchase.order"].browse(order_id)
    #     if order:
    #
    #         for data in data_list:
    #
    #             product_id = data["values"].get("product_id", "")
    #
    #
    #             line = order.order_line.filtered(lambda l: l.product_id.id == product_id)
    #             if line:
    #                 data["values"]["id"] = str(line[0].id)
    #
    #
    #
    #     return super()._load_records(data_list, update)

    @api.model
    def load(self, fields, data):
        order = self.env["sale.order"]
        order_id = self.env.context.get("default_order_id", False) or self.env.context.get("active_id", False)
        if order_id:
            order = self.env["sale.order"].browse(order_id)

        if not order:
            order_index = fields.index("order_id") if "order_id" in fields else False
            if order_index is not False:
                order_id = data[0][order_index]
                order = self.env["sale.order"].browse(order_id)

        if order:
            if order.order_line:
                product_index = fields.index("product_id") if "product_id" in fields else -1
                fields.append(".id")
                index_id = fields.index(".id")
                for record in data:
                    record.append("")

                if product_index != -1:
                    for record in list(data):
                        product_name = record[product_index]
                        product = self.env["product.product"]
                        # extrage codul din numele produsului care este intre paranteze []
                        if "[" in product_name and "]" in product_name:
                            product_code = product_name.split("[")[-1].split("]")[0].strip()
                            product = self.env["product.product"].search([("default_code", "=", product_code)], limit=1)
                        if not product:
                            product_name = product_name.split("[")[0].strip()
                            product = self.env["product.product"].search([("name", "=", product_name)], limit=1)

                        if not product:
                            data.remove(record)
                            continue
                        if product:
                            line = order.order_line.filtered(lambda l: l.product_id.id == product.id)
                            if line:
                                record[index_id] = str(line.id)
                            else:
                                data.remove(record)
            else:
                # product_index = fields.index("product_id") if "product_id" in fields else -1
                # for record in data:
                #     product_name = record[product_index]
                #     product = self.env["product.product"]
                #     # extrage codul din numele produsului care este intre paranteze []
                #     if "[" in product_name and "]" in product_name:
                #         product_code = product_name.split("[")[-1].split("]")[0].strip()
                #         product = self.env["product.product"].search([("default_code", "=", product_code)], limit=1)
                #     if product_name.is_digit():
                #         product = self.env["product.product"].search([("default_code", "=", product_name)], limit=1)
                #         if not product:
                #             product = self.env["product.product"].search([("barcode", "=", product_name)], limit=1)

                # din teste pare ca nu trebuie cautat produsul separat dupa cod de bare/referinta
                fields.append("order_id")
                price_index = fields.index("price_unit") if "price_unit" in fields else -1
                if price_index != -1:
                    self.use_specific_price_formula(data, price_index)
                for record in data:
                    record.append(order.name)

        return super().load(fields, data)

    def use_specific_price_formula(self, data, price_index):
        """Some clients may use this import with different price formulas, and it would be easier to make the formula on their database specific modules instead of trying to incorporate it in the general module."""
        return
