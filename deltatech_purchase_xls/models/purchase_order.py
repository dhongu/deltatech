# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def show_order_lines(self):
        """Override to show order lines in the XLS report."""
        self.ensure_one()

        tree_view_id = self.env.ref("deltatech_purchase_xls.purchase_order_line_tree").id
        return {
            "type": "ir.actions.act_window",
            "name": "Purchase Order Lines",
            "res_model": "purchase.order.line",
            "view_mode": "list,form",
            "views": [(tree_view_id, "list")],
            "domain": [("order_id", "=", self.id)],
            "context": {"default_order_id": self.id, "create": True, "edit": True},
        }


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

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
    def _get_import_order(self, fields, data):
        """Return the purchase order the imported rows belong to.

        The order comes from ``default_order_id`` / ``active_id`` in the context or, failing that, from the
        order column of the file (``order_id`` by name, ``order_id/id`` by external id, ``order_id/.id`` by
        database id). The column is used only when all the rows point to one existing order; otherwise an
        empty recordset is returned and the rows are left to the standard import.
        """
        order_model = self.env["purchase.order"]
        order_id = self.env.context.get("default_order_id", False) or self.env.context.get("active_id", False)
        if order_id:
            return order_model.browse(order_id)

        for field_name in ("order_id", "order_id/id", "order_id/.id"):
            if field_name not in fields:
                continue
            order_index = fields.index(field_name)
            values = {str(record[order_index]).strip() for record in data if record[order_index] not in (False, None)}
            values.discard("")
            if len(values) != 1:
                return order_model
            value = values.pop()
            if field_name == "order_id":
                return order_model.search([("name", "=", value)], limit=1)
            if field_name == "order_id/id":
                if "." not in value:
                    value = f"__import__.{value}"
                record = self.env.ref(value, raise_if_not_found=False)
                return record if record and record._name == "purchase.order" else order_model
            return order_model.browse(int(value)).exists() if value.isdigit() else order_model
        return order_model

    @api.model
    def _get_import_product(self, value):
        """Find the product of an imported row: by the code between ``[]`` and then by name."""
        product = self.env["product.product"]
        if value is None or isinstance(value, bool):
            return product
        value = str(value).strip()
        if not value:
            return product
        # extrage codul din numele produsului care este intre paranteze []
        if "[" in value and "]" in value:
            product_code = value.split("[")[-1].split("]")[0].strip()
            product = product.search([("default_code", "=", product_code)], limit=1)
        if not product:
            product_name = value.split("[")[0].strip()
            if product_name:
                product = product.search([("name", "=", product_name)], limit=1)
        return product

    @api.model
    def load(self, fields, data):
        """Import lines in the order given by the context or by the order column of the file.

        When the order already has lines, only those lines are updated: each row is matched by product
        to a line of the order and the rows without a match are dropped. When several lines have the same
        product, the rows are matched in order to the first line not used yet by a previous row; a row
        left without a free line is dropped. When the order has no lines, the rows are created as new
        lines of the order.
        """
        order = self._get_import_order(fields, data)

        if order:
            fields = list(fields)
            if order.order_line:
                product_index = fields.index("product_id") if "product_id" in fields else -1
                if ".id" not in fields:
                    fields.append(".id")
                    data = [list(record) + [""] for record in data]
                index_id = fields.index(".id")

                if product_index != -1:
                    rows = []
                    used_lines = self.env["purchase.order.line"]
                    for record in data:
                        product = self._get_import_product(record[product_index])
                        if not product:
                            continue
                        line = (order.order_line - used_lines).filtered(lambda l: l.product_id == product)[:1]
                        if not line:
                            continue
                        used_lines |= line
                        record = list(record)
                        record[index_id] = str(line.id)
                        rows.append(record)
                    data = rows
            elif not any(name in fields for name in ("order_id", "order_id/id", "order_id/.id")):
                # din teste pare ca nu trebuie cautat produsul separat dupa cod de bare/referinta
                fields.append("order_id")
                data = [list(record) + [order.name] for record in data]

        return super().load(fields, data)
