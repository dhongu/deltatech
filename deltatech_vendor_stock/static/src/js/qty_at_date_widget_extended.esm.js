import {QtyAtDatePopover, QtyAtDateWidget, qtyAtDateWidget} from "@sale_stock/widgets/qty_at_date_widget";
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

// Load the fields read by the popover whatever the order line view declares
qtyAtDateWidget.fieldDependencies.push(
    {name: "company_id", type: "many2one"},
    {name: "product_uom_id", type: "many2one"},
    {name: "product_uom_qty", type: "float"},
    {name: "vendor_qty_available", type: "float"},
    {name: "other_qty_available", type: "float"}
);

patch(QtyAtDateWidget.prototype, {
    setup() {
        super.setup();
        this.colorsService = useService("vendor_stock_colors");
        this.stockColors = DEFAULT_COLORS;

        onWillStart(async () => {
            this.stockColors = await this.colorsService.getColors();
        });
    },

    async calcDataForDisplay(calcData) {
        await super.calcDataForDisplay(calcData);
        // Read only when the popover opens, not for every line of the order
        const {data} = this.props.record;
        calcData.warehouse_stock = [];
        if (data.product_id) {
            calcData.warehouse_stock = await this.orm.call(
                "sale.order.line",
                "get_warehouse_stock",
                [data.product_id.id],
                {
                    uom_id: data.product_uom_id?.id || false,
                    company_id: data.company_id?.id || false,
                    warehouse_id: data.warehouse_id?.id || false,
                }
            );
        }
    },
});

patch(QtyAtDatePopover.prototype, {
    get warehouseDemand() {
        const {data} = this.props.record;
        return data.qty_to_deliver ?? data.product_uom_qty ?? 0;
    },

    warehouseStockClass(row) {
        if (row.qty >= this.warehouseDemand) {
            return "text-success";
        }
        return row.is_order_warehouse ? "text-danger" : "";
    },

    openWarehouseForecast(row) {
        const {data} = this.props.record;
        const context = {
            active_model: "product.product",
            active_id: data.product_id.id,
            warehouse_id: row.warehouse_id,
        };
        if (row.is_order_warehouse) {
            context.move_to_match_ids = data.move_ids.currentIds;
            context.sale_line_to_match_id = this.props.record.resId;
        }
        this.actionService.doAction("stock.stock_forecasted_product_product_action", {
            additionalContext: context,
        });
    },
});
