/** @odoo-module **/

import {PosOrder} from "@point_of_sale/app/models/pos_order";
import {PosOrderline} from "@point_of_sale/app/models/pos_order_line";
import {PosStore} from "@point_of_sale/app/services/pos_store";
import {patch} from "@web/core/utils/patch";

/**
 * Since 19.0 the POS builds a line from `vals.product_tmpl_id`, not from
 * `vals.product_id` - the variant is derived from the template. Read the
 * template from whichever of the two the caller provided.
 */
function getProductTemplate(store, vals) {
    let template = vals.product_tmpl_id;
    if (typeof template === "number") {
        template = store.data.models["product.template"].get(template);
    }
    if (!template) {
        let product = vals.product_id;
        if (typeof product === "number") {
            product = store.data.models["product.product"].get(product);
        }
        template = product?.product_tmpl_id;
    }
    return template;
}

patch(PosStore.prototype, {
    async addLineToCurrentOrder(vals, opt = {}, configure = true) {
        const line = await super.addLineToCurrentOrder(vals, opt, configure);

        const product_tmpl = getProductTemplate(this, vals);
        const extra_product_id = product_tmpl?.extra_product_id;

        // The extra product is only reachable when it is itself loaded in the
        // POS - it has to be available in the point of sale.
        if (extra_product_id?.product_tmpl_id) {
            const order = this.getOrder();
            const extra_line = order.add_extra_product(extra_product_id);
            if (!extra_line) {
                let qty = vals.qty || 1;
                qty *= product_tmpl.extra_qty || 1;
                await this.addLineToCurrentOrder({
                    product_tmpl_id: extra_product_id.product_tmpl_id,
                    product_id: extra_product_id,
                    qty: qty,
                });
            }
        }
        return line;
    },
});

patch(PosOrder.prototype, {
    add_extra_product(extra_product_id) {
        let extra_line = false;
        let qty = 0;

        for (const line of this.lines) {
            const line_extra_product = line.product_id?.product_tmpl_id?.extra_product_id;
            if (line_extra_product) {
                if (line_extra_product.id === extra_product_id.id) {
                    qty += line.qty * (line.product_id.product_tmpl_id.extra_qty || 1);
                }
            }
            if (line.product_id?.id === extra_product_id.id) {
                line.qty = 0;
                extra_line = line;
            }
        }
        if (extra_line !== false) {
            extra_line.setQuantity(qty, true);
        }
        return extra_line;
    },
});

patch(PosOrderline.prototype, {
    setQuantity(quantity, keep_price) {
        const res = super.setQuantity(quantity, keep_price);
        const extra_product_id = this.product_id?.product_tmpl_id?.extra_product_id;
        if (extra_product_id) {
            const order = this.order_id;
            order.add_extra_product(extra_product_id);
        }
        return res;
    },
});
