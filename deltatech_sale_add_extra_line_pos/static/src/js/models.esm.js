/** @odoo-module **/

import {Order, Orderline} from "@point_of_sale/app/store/models";
import {patch} from "@web/core/utils/patch";

patch(Orderline.prototype, {
    set_quantity(...args) {
        const res = super.set_quantity(...args);
        if (this.product.extra_product_id) {
            const extra_product_id = this.pos.db.get_product_by_id(this.product.extra_product_id[0]);
            if (extra_product_id) {
                this.order.add_extra_product(extra_product_id);
            }
        }
        return res;
    },
});

patch(Order.prototype, {
    add_product(product, ...args) {
        const res = super.add_product(product, ...args);
        if (product.extra_product_id) {
            const extra_product_id = this.pos.db.get_product_by_id(product.extra_product_id[0]);
            if (extra_product_id) {
                this.add_extra_product(extra_product_id);
            }
        }
        return res;
    },
    add_extra_product(extra_product_id) {
        let extra_line = false;
        let qty = 0;
        let options = {};
        for (const line of this.get_orderlines()) {
            if (line.product.extra_product_id) {
                if (line.product.extra_product_id[0] === extra_product_id.id) {
                    qty += line.quantity * line.product.extra_qty;
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
