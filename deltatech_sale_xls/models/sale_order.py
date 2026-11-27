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
            "name": self.env._("Order Lines"),
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
            if order_index is not False and data:
                order = self._find_import_order(data[0][order_index])

        if order:
            if order.order_line:
                product_index = fields.index("product_id") if "product_id" in fields else -1
                if ".id" not in fields:
                    fields.append(".id")
                    for record in data:
                        record.append("")
                index_id = fields.index(".id")

                # the IDs are checked even without a product column
                errors = self._match_import_lines(order, fields, data, product_index, index_id)
                if errors:
                    return {"ids": False, "messages": errors, "nextrow": 0}
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
                price_index = fields.index("price_unit") if "price_unit" in fields else -1
                if price_index != -1:
                    self.use_specific_price_formula(data, price_index)
                # every row goes into this order, even when the file has its own order column
                if "order_id" in fields:
                    order_index = fields.index("order_id")
                    for record in data:
                        record[order_index] = order.name
                else:
                    fields.append("order_id")
                    for record in data:
                        record.append(order.name)

        return super().load(fields, data)

    @api.model
    def _find_import_order(self, value):
        """Order from the ``order_id`` cell: its database id (number) or its reference (``S00039``)."""
        orders = self.env["sale.order"]
        if isinstance(value, int) or str(value or "").strip().isdigit():
            return orders.browse(int(value)).exists()
        if value:
            return orders.search([("name", "=", str(value).strip())], limit=1)
        return orders

    @api.model
    def _resolve_import_xid(self, xid):
        """Database id of the order line named by the external id of an import row, or ``False``."""
        xid = str(xid).strip()
        if "." not in xid:
            xid = f"__import__.{xid}"
        model, res_id = self.env["ir.model.data"]._xmlid_to_res_model_res_id(xid, raise_if_not_found=False)
        return res_id if model == self._name else False

    @api.model
    def _find_import_product(self, product_name):
        """Product from the import cell: ``[CODE] Name`` by internal reference, else by exact name."""
        product = self.env["product.product"]
        product_name = product_name or ""
        if "[" in product_name and "]" in product_name:
            product_code = product_name.split("[")[-1].split("]")[0].strip()
            product = product.search([("default_code", "=", product_code)], limit=1)
        if not product:
            product_name = product_name.split("[")[0].strip()
            product = product.search([("name", "=", product_name)], limit=1)
        return product

    @api.model
    def _match_import_lines(self, order, fields, data, product_index, index_id):
        """Fill the ``.id`` column of the rows with the order line they update.

        Rows that already carry a database id (``.id``) or an external id (``id``) keep it; their
        lines are taken first, and a line named by two rows is an error.
        The other rows are matched by product among the order lines not taken yet; when several
        lines have the product, the ``name`` (description) column narrows the match. A row that
        still matches several lines is not assigned arbitrarily: an import error is returned.
        A product with more rows than order lines is an error too. Rows with an unknown product,
        or a product that is not on the order, are dropped.
        """
        xid_index = fields.index("id") if "id" in fields else -1
        name_index = fields.index("name") if "name" in fields else -1

        def explicit_line_id(record):
            """Line id given by the row (``.id`` or external id), ``False`` when the row has none."""
            if record[index_id]:
                return int(record[index_id]) if str(record[index_id]).strip().isdigit() else -1
            if xid_index != -1 and record[xid_index]:
                return self._resolve_import_xid(record[xid_index]) or -1
            return False

        def error(row, record, message):
            # ``field`` and ``value`` attach the error to the product column of the import screen
            value = record[product_index] if product_index != -1 else ""
            return {
                "type": "error",
                "record": row,
                "rows": {"from": row, "to": row},
                "field": "product_id",
                "value": value,
                "message": message,
            }

        # the lines named by an ID are taken first, so that the rows without ID cannot reuse them
        used = self.env["sale.order.line"]
        errors = []
        for row, record in enumerate(data):
            line_id = explicit_line_id(record)
            if not line_id:
                continue
            line = order.order_line.filtered(lambda line, line_id=line_id: line.id == line_id)
            if not line:
                # a deleted line (its external id is gone) or a line of another order: the standard
                # load would create a new line or change the other order
                errors.append(
                    error(
                        row,
                        record,
                        self.env._(
                            "The ID of this row is not a line of order %(order)s: the line was deleted "
                            "after the export, or the file belongs to another order. Remove the row, or "
                            "clear its ID to match it by product.",
                            order=order.name,
                        ),
                    )
                )
                continue
            if line in used:
                errors.append(
                    error(
                        row,
                        record,
                        self.env._(
                            "Line %(line)s of order %(order)s is on several rows of the file. Each line can "
                            "be updated by one row only: add the new line in the order first.",
                            line=line.name,
                            order=order.name,
                        ),
                    )
                )
            used |= line
        if product_index == -1:
            # without a product column the rows without ID cannot be matched: left to the standard load
            return errors
        for row, record in enumerate(list(data)):
            if explicit_line_id(record):
                continue
            product = self._find_import_product(record[product_index])
            product_lines = order.order_line.filtered(lambda line: product and line.product_id == product)
            if not product_lines:
                data.remove(record)
                continue
            candidates = product_lines - used
            if len(candidates) > 1 and name_index != -1 and record[name_index]:
                by_name = candidates.filtered(lambda line: line.name == record[name_index])
                candidates = by_name or candidates
            if len(candidates) == 1:
                record[index_id] = str(candidates.id)
                used |= candidates
                continue
            if candidates:
                message = self.env._(
                    "Product %(product)s is on %(count)s lines of order %(order)s, so the row cannot be "
                    "matched to a single line. Add the External ID column (export the lines with it) or "
                    "the Description column to identify the line.",
                    product=product.display_name,
                    count=len(candidates),
                    order=order.name,
                )
            else:
                message = self.env._(
                    "The file has more rows for product %(product)s than the %(count)s line(s) of order "
                    "%(order)s that have it. Add the External ID column (export the lines with it) to "
                    "identify the line of each row.",
                    product=product.display_name,
                    count=len(product_lines),
                    order=order.name,
                )
            errors.append(error(row, record, message))
        return errors

    def use_specific_price_formula(self, data, price_index):
        """Some clients may use this import with different price formulas, and it would be easier to make the formula on their database specific modules instead of trying to incorporate it in the general module."""
        return
