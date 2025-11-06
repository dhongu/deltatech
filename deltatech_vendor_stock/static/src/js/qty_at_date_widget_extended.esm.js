import {QtyAtDateWidget} from "@sale_stock/widgets/qty_at_date_widget";
import {onWillStart} from "@odoo/owl";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";

const DEFAULT_COLORS = {
    color_fulfilled: "#28a745",
    color_fulfilled_no_free_qty: "#17a2b8",
    color_not_fulfilled: "#dc3545",
    color_vendor_available: "#ffc107",
    color_default: "#007bff",
};

patch(QtyAtDateWidget.prototype, {
    setup() {
        super.setup();
        this.colorsService = useService("vendor_stock_colors");
        this.stockColors = DEFAULT_COLORS;

        onWillStart(async () => {
            this.stockColors = await this.colorsService.getColors();
        });
    },
});
