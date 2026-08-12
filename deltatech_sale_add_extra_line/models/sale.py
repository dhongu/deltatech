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

    def unlink(self):
        for line in self:
            if line._get_extra_product():
                extra_line_id = self.order_id.order_line.filtered(
                    lambda li, line_uuid=line.line_uuid, line_id=line.id: li.line_uuid is not False
                    and li.line_uuid == line_uuid
                    and li.id != line_id
                )
                if extra_line_id:
                    extra_line_id.unlink()
        return super().unlink()

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
        for line in self:
            extra_product = line._get_extra_product()
            if extra_product:
                extra_line_id = self.order_id.order_line.filtered(
                    lambda li, line_uuid=line.line_uuid, line_id=line.id: li.line_uuid is not False
                    and li.line_uuid == line_uuid
                    and li.id != line_id
                )
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
