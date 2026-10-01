# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


import uuid

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("order_line")
    def onchange_order_line(self):
        """
        Update extra product in backend
        :return: super
        """
        self.order_line.with_context(backend=True).check_extra_product()

    def _verify_cart_after_update(self):
        # În Odoo 19 API-ul website_sale a fost refactorizat: `_cart_update` nu mai
        # există. Hook-ul `_verify_cart_after_update` este apelat după `_cart_add` și
        # după `_cart_update_line_quantity`, deci e locul în care coșul din magazinul
        # online primește linia suplimentară.
        # Hook-ul nu primește linia atinsă, așa că se resincronizează toate liniile
        # comenzii — echivalentul ramurii „seems like delete" din vechiul `_cart_update`.
        # Liniile șterse din coș (cantitate 0) nu mai apar aici, iar linia extra a fost
        # deja ștearsă împreună cu linia principală de `SaleOrderLine.unlink`.
        # Se rulează înaintea super() ca prețul livrării și `cart_quantity` din sesiune,
        # calculate acolo, să țină cont de liniile suplimentare.
        # Fără `backend=True` în context, liniile extra se creează prin `create()`, deci
        # există în bază imediat după actualizarea coșului.
        self.order_line.check_extra_product()
        return super()._verify_cart_after_update()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    line_uuid = fields.Char()
    is_extra_line = fields.Boolean(
        help="Technical field: the line was generated as the extra line of the main line "
        "sharing its UUID. It is removed or replaced together with that main line.",
    )
    extra_price_computed = fields.Float(
        digits="Product Price",
        copy=False,
        help="Technical field: last unit price computed for this extra line. "
        "A unit price that differs from it was set by the user and is kept as is.",
    )

    def _get_extra_product(self):
        """Return the product the extra line of this line must carry.

        By default the one set on the product itself, but a module can decide it
        from the line instead - the extra product then no longer has to be filled
        in on every product for the line to appear.
        """
        self.ensure_one()
        return self.product_id.extra_product_id

    def _get_extra_line(self):
        """Return the generated extra line paired with this main line, if any."""
        self.ensure_one()
        if self.is_extra_line or not self.line_uuid:
            return self.browse()
        return self.order_id.order_line.filtered(
            lambda li, line_uuid=self.line_uuid, line_id=self.id: li.is_extra_line
            and li.line_uuid == line_uuid
            and li.id != line_id
        )

    def _remove_extra_line(self, extra_line):
        """Drop an extra line that no longer matches its main line."""
        if self.env.context.get("backend", False):
            # in the form, the line is taken out of the order and deleted on save
            self.order_id.order_line -= extra_line
        else:
            extra_line.unlink()

    def unlink(self):
        # the pair is found through the flag, not through the current configuration of the
        # product: the main line may have changed product or the product its extra product.
        # On save, the form may send a delete for an extra line already deleted with its
        # main line, hence `exists()`
        lines = self.exists()
        extra_lines = self.browse()
        for line in lines:
            extra_lines |= line._get_extra_line()
        extra_lines -= lines
        if extra_lines:
            extra_lines.unlink()
        return super(SaleOrderLine, lines).unlink()

    def _has_manual_price(self):
        """Tell whether the unit price of this extra line was set by the user.

        The price is considered manual when it matches neither what this module
        computed last (``extra_price_computed``) nor what the standard price
        computation wrote (``technical_price_unit``, kept equal to ``price_unit``
        by ``_reset_price_unit``, so a pricelist recomputation is not mistaken
        for a manual price).
        """
        self.ensure_one()
        # `currency_id` can be False on NewId records
        currency = self.currency_id or self.company_id.currency_id or self.env.company.currency_id
        return bool(
            currency.compare_amounts(self.extra_price_computed, self.price_unit)
            and currency.compare_amounts(self.technical_price_unit, self.price_unit)
        )

    def check_extra_product(self):
        # an extra line does not get an extra line of its own; filtered upfront, as the
        # loop may delete extra lines that are still in `self`
        for line in self.filtered(lambda li: not li.is_extra_line):
            extra_product = line._get_extra_product()
            extra_line_id = line._get_extra_line()
            if extra_line_id and extra_line_id.product_id != extra_product:
                # the main line changed product (or its product changed extra product):
                # the old extra line goes, and the right one is generated below, with the
                # computed price - a manual price belonged to the old extra product
                line._remove_extra_line(extra_line_id)
                extra_line_id = self.browse()
            if extra_product:
                new_line = not extra_line_id
                if new_line:
                    new_uuid = str(uuid.uuid4())
                    values = {
                        "product_uom_qty": line.product_uom_qty * (line.product_id.extra_qty or 1.0),
                        "product_id": extra_product.id,
                        "state": "draft",
                        "order_id": line.order_id.id,
                        "sequence": line.sequence + 1,
                        "line_uuid": new_uuid,
                        "is_extra_line": True,
                    }
                    backend = self.env.context.get("backend", False)
                    if backend:
                        extra_line_id = line.order_id.order_line.new(values)
                    else:
                        extra_line_id = line.order_id.order_line.create(values)
                    line.line_uuid = new_uuid

                extra_line_id.product_uom_qty = line.product_uom_qty * (line.product_id.extra_qty or 1.0)
                # a price typed in on the extra line wins over the computed one, until the
                # extra line is deleted (it is then regenerated with the computed price)
                if not new_line and extra_line_id._has_manual_price():
                    continue
                if not line.product_id.extra_percent:
                    # no percent: the standard price computation applies, so the extra line
                    # gets the price of its own product in the pricelist, currency and unit
                    # of measure of the order
                    continue
                price_unit = line.price_unit * (line.product_id.extra_percent or 0.0) / 100.0
                # keep track of the price we set, so that a later manual change is recognized
                extra_line_id.update({"price_unit": price_unit, "extra_price_computed": price_unit})
