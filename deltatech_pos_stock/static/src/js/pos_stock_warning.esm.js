/** @odoo-module **/

import {PosStore} from "@point_of_sale/app/services/pos_store";
import {patch} from "@web/core/utils/patch";
import {_t} from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    /**
     * Warn, but do not block, when a product with no stock left is added.
     *
     * A hard block would stop the cashier selling whenever the figure in Odoo is behind -
     * van stock, or parts not yet booked in - which costs more than it saves. The register
     * says what it knows and lets the person decide.
     */
    async addLineToCurrentOrder(vals, opts = {}, configure = true) {
        this._warnIfOutOfStock(vals);
        return await super.addLineToCurrentOrder(vals, opts, configure);
    },

    _warnIfOutOfStock(vals) {
        const config = this.config;
        if (!config?.display_stock) {
            return;
        }
        const template = vals?.product_tmpl_id || vals?.product_id?.product_tmpl_id;
        if (!template?.is_storable) {
            return;
        }
        const useFreeQty = config.stock_badge_quantity === "available";
        const quantity = (useFreeQty ? template.free_qty : template.qty_available) || 0;
        if (quantity > 0) {
            return;
        }
        this.notification.add(_t("%s is out of stock.", template.display_name), {
            type: "warning",
        });
    },
});
