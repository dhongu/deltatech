import {Interaction} from "@web/public/interaction";
import {registry} from "@web/core/registry";

const ICONS = {
    in_stock: "fa-check-circle",
    on_order: "fa-clock-o",
    out: "fa-times-circle",
};

// The stock of every warehouse is already in the page (data attributes of the
// options): the button only shows the message of the selected warehouse.
export class WarehouseStockSelector extends Interaction {
    static selector = ".o_wh_stock_selector";
    dynamicContent = {
        ".o_wh_stock_check": {"t-on-click": this.onCheck},
        ".o_wh_stock_select": {"t-on-change": this.onCheck},
    };

    onCheck() {
        const select = this.el.querySelector(".o_wh_stock_select");
        const option = select.options[select.selectedIndex];
        if (!option) {
            return;
        }
        const state = option.dataset.state;
        const result = this.el.querySelector(".o_wh_stock_result");
        result.className = `o_wh_stock_result mt-2 o_wh_stock_state_${state}`;
        result.querySelector(".o_wh_stock_icon").className = `o_wh_stock_icon fa fa-fw ${ICONS[state] || ""}`;
        result.querySelector(".o_wh_stock_message").textContent = option.dataset.message || "";
        result.querySelector(".o_wh_stock_note").textContent = option.dataset.note || "";
    }
}

registry
    .category("public.interactions")
    .add("deltatech_website_warehouse_stock.warehouse_stock_selector", WarehouseStockSelector);
