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
        // The main line was not added: configurator, lot or weight popup
        // cancelled, or a refund constraint refused it - no extra line either.
        if (!line) {
            return line;
        }

        const product_tmpl = getProductTemplate(this, vals);
        const extra_product_id = product_tmpl?.extra_product_id;

        // The extra product is only reachable when it is itself loaded in the
        // POS - it has to be available in the point of sale.
        if (extra_product_id?.product_tmpl_id) {
            const order = line.order_id || this.getOrder();
            const extra_line = order.add_extra_product(extra_product_id);
            if (!extra_line) {
                // The quantity comes from the lines the order actually holds
                // (weighed, negative in a return, merged with an existing
                // line), not from the quantity that was requested.
                const qty = order.getExtraProductDemand(extra_product_id);
                if (qty) {
                    await this.addLineToCurrentOrder({
                        product_tmpl_id: extra_product_id.product_tmpl_id,
                        product_id: extra_product_id,
                        qty: qty,
                    });
                }
            }
        }
        return line;
    },
});

patch(PosOrder.prototype, {
    /**
     * Quantity of `extra_product_id` that the main lines of the order ask for.
     */
    getExtraProductDemand(extra_product_id) {
        let qty = 0;
        for (const line of this.lines) {
            const product_tmpl = line.product_id?.product_tmpl_id;
            if (product_tmpl?.extra_product_id?.id === extra_product_id.id) {
                qty += line.qty * (product_tmpl.extra_qty || 1);
            }
        }
        return qty;
    },

    getExtraProductLine(extra_product_id) {
        return this.lines.find((line) => line.product_id?.id === extra_product_id.id) || false;
    },

    add_extra_product(extra_product_id) {
        const extra_line = this.getExtraProductLine(extra_product_id);
        if (extra_line !== false) {
            extra_line.setQuantity(this.getExtraProductDemand(extra_product_id), true);
        }
        return extra_line;
    },

    removeOrderline(line, deep = true) {
        // The extra products of the removed lines; the deletion does not go
        // through setQuantity, so their quantity has to be synchronised here.
        const removed_lines = deep ? line.getAllLinesInCombo() : [line];
        const extra_products = removed_lines
            .map((removed) => removed.product_id?.product_tmpl_id?.extra_product_id)
            .filter((extra_product_id) => extra_product_id?.id);
        const res = super.removeOrderline(line, deep);
        for (const extra_product_id of extra_products) {
            const extra_line = this.getExtraProductLine(extra_product_id);
            if (!extra_line) {
                continue;
            }
            if (this.getExtraProductDemand(extra_product_id)) {
                this.add_extra_product(extra_product_id);
            } else {
                // No main line asks for it any more: drop the generated line.
                super.removeOrderline(extra_line);
            }
        }
        return res;
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
