odoo.define("deltatech_sale_add_extra_line_pos.models", function (require) {
    "use strict";

    const {Orderline, Order} = require("point_of_sale.models");
    const Registries = require("point_of_sale.Registries");

    const PosExtraLineOrderline = (Orderline) =>
        class PosExtraLineOrderline extends Orderline {
            set_quantity() {
                var res = super.set_quantity(...arguments);
                if (this.product.extra_product_id) {
                    var extra_product_id = this.pos.db.get_product_by_id(this.product.extra_product_id[0]);
                    this.order.add_extra_product(extra_product_id);
                }
                return res;
            }
        };

    Registries.Model.extend(Orderline, PosExtraLineOrderline);

    const PosExtraLineOrder = (Order) =>
        class PosExtraLineOrder extends Order {
            add_product(product) {
                var res = super.add_product(...arguments);
                if (product.extra_product_id) {
                    var extra_product_id = this.pos.db.get_product_by_id(product.extra_product_id[0]);
                    this.add_extra_product(extra_product_id);
                }
                return res;
            }

            add_extra_product(extra_product_id) {
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
            }
        };
    Registries.Model.extend(Order, PosExtraLineOrder);
});
