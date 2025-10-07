/** @odoo-module **/

import {registry} from "@web/core/registry";
import {jsonrpc} from "@web/core/network/rpc_service";

const DEFAULT_COLORS = {
    color_fulfilled: "#28a745",
    color_fulfilled_no_free_qty: "#17a2b8",
    color_not_fulfilled: "#dc3545",
    color_vendor_available: "#ffc107",
    color_default: "#007bff",
};

registry.category("services").add("vendor_stock_colors", {
    start() {
        let colorsPromise = null;

        const load = async () => {
            const colors = await jsonrpc("/web/dataset/call_kw", {
                model: "sale.order.line",
                method: "get_stock_colors",
                args: [],
                kwargs: {},
            });
            return colors;
        };

        return {
            async getColors() {
                if (!colorsPromise) {
                    colorsPromise = load().catch((e) => {
                        // Reset cache on failure to allow retry next time
                        colorsPromise = null;
                        throw e;
                    });
                }
                try {
                    return await colorsPromise;
                } catch (e) {
                    console.warn("Failed to load stock colors, using defaults:", e);
                    return DEFAULT_COLORS;
                }
            },
            invalidate() {
                colorsPromise = null;
            },
        };
    },
});
