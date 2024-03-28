odoo.define("deltatech_sale_add_extra_line_pos.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");

    models.load_fields("product.product", ["extra_product_id"]);

    var Orderline = models.Orderline;
    models.Orderline = models.Orderline.extend({
        initialize: function () {
            Orderline.prototype.initialize.apply(this, arguments);
        },
        set_quantity: function () {
            Orderline.prototype.set_quantity.apply(this, arguments);
            if (this.product.extra_product_id) {
                var extra_product_id = this.pos.db.get_product_by_id(this.product.extra_product_id[0]);
                this.order.add_extra_product(extra_product_id);
            }
        },
    });

    var Order = models.Order;
    models.Order = models.Order.extend({
        initialize: function () {
            Order.prototype.initialize.apply(this, arguments);
        },
        add_product: function (product) {
            Order.prototype.add_product.apply(this, arguments);
            if (product.extra_product_id) {
                var extra_product_id = this.pos.db.get_product_by_id(product.extra_product_id[0]);
                this.add_extra_product(extra_product_id);
            }
        },

        add_extra_product: function (extra_product_id) {
            var extra_line = false;
            var qty = 0;
            var options = {};
            for (const line of this.get_orderlines()) {
                if (line.product.extra_product_id) {
                    if (line.product.extra_product_id[0] === extra_product_id.id) {
                        qty += line.quantity;
                    }
                }
                if (line.product.id === extra_product_id.id) {
                    line.quantity = 0;
                    extra_line = line;
                }
            }
            if (extra_line !== false) {
                extra_line.set_quantity(qty);
            } else {
                options = {quantity: qty};
                this.add_product(extra_product_id, options);
            }
        },
    });
});
