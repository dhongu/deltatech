/** @odoo-module **/
import {registry} from "@web/core/registry";

const DEFAULT_COLORS = {
    color_fulfilled: "#28a745",
    color_fulfilled_no_free_qty: "#17a2b8",
    color_not_fulfilled: "#dc3545",
    color_vendor_available: "#ffc107",
    color_default: "#007bff",
};

registry.category("services").add("vendor_stock_colors", {
    dependencies: ["orm"],
    start(env, {orm}) {
        let colorsPromise = null;

        const load = () => orm.call("sale.order.line", "get_stock_colors", []);

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
