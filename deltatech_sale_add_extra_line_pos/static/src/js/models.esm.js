/** @odoo-module **/

import {PosOrder} from "@point_of_sale/app/models/pos_order";
import {PosOrderline} from "@point_of_sale/app/models/pos_order_line";
import {PosStore} from "@point_of_sale/app/store/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async addLineToCurrentOrder(vals, opt = {}, configure = true) {
        await super.addLineToCurrentOrder(vals, opt, configure);

        const product = vals.product_id;
        const extra_product_id = product.product_tmpl_id.extra_product_id;

        if (extra_product_id) {
            const order = this.get_order();
            const extra_line = order.add_extra_product(extra_product_id);
            if (!extra_line) {
                let qty = vals.qty || 1;
                qty *= product.product_tmpl_id.extra_qty;
                this.addLineToCurrentOrder({product_id: extra_product_id, qty: qty});
            }
        }
    },
});

patch(PosOrder.prototype, {
    add_extra_product(extra_product_id) {
        let extra_line = false;
        let qty = 0;

        for (const line of this.lines) {
            const line_extra_product = line.product_id.product_tmpl_id.extra_product_id;
            if (line_extra_product) {
                if (line_extra_product.id === extra_product_id.id) {
                    qty += line.qty * line.product_id.product_tmpl_id.extra_qty;
                }
            }
            if (line.product_id.id === extra_product_id.id) {
                line.qty = 0;
                extra_line = line;
            }
        }
        if (extra_line !== false) {
            extra_line.set_quantity(qty, true);
        }
        return extra_line;
    },
});

patch(PosOrderline.prototype, {
    set_quantity(quantity, keep_price) {
        const res = super.set_quantity(quantity, keep_price);
        const extra_product_id = this.product_id.product_tmpl_id.extra_product_id;
        if (extra_product_id) {
            const order = this.order_id;
            order.add_extra_product(extra_product_id);
        }
        return res;
    },
});
