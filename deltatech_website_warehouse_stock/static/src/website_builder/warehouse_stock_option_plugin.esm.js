import {BaseOptionComponent} from "@html_builder/core/base_option_component";
import {BuilderAction} from "@html_builder/core/builder_action";
import {Plugin} from "@html_editor/plugin";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";

// Field of the website -> data attribute of the block with its current value
const DATA_KEYS = {
    warehouse_stock_position: "whPosition",
    warehouse_stock_style: "whStyle",
    warehouse_stock_zero_message: "whZero",
    warehouse_stock_qty_display: "whQty",
    warehouse_stock_theme_colors: "whTheme",
};

const BOOLEAN_FIELDS = ["warehouse_stock_theme_colors"];

// Selector, title and groups are in the option declaration (website.BuilderOptions)
export class WarehouseStockOption extends BaseOptionComponent {
    static id = "warehouse_stock_option";
    static template = "deltatech_website_warehouse_stock.WarehouseStockOption";
}

// The options are settings of the website (also in Website > Configuration > Settings):
// the value is written on the website and the page is reloaded to render the block again.
export class WarehouseStockConfigAction extends BuilderAction {
    static id = "warehouseStockConfig";

    setup() {
        this.reload = {};
    }

    getValue({editingElement, params: {mainParam: field}}) {
        return editingElement.dataset[DATA_KEYS[field]];
    }

    isApplied({editingElement, params: {mainParam: field}, value}) {
        // A checkbox has no value: it is applied when the option is on
        return editingElement.dataset[DATA_KEYS[field]] === (value === undefined ? "1" : value);
    }

    async apply({params: {mainParam: field}, value}) {
        await rpc("/website/warehouse_stock/config", {field, value: value === undefined ? "1" : value});
    }

    async clean({params: {mainParam: field}}) {
        // A select cleans the previous item before applying the new one: only the
        // checkbox (boolean) has something to switch off.
        if (BOOLEAN_FIELDS.includes(field)) {
            await rpc("/website/warehouse_stock/config", {field, value: "0"});
        }
    }
}

class WarehouseStockOptionPlugin extends Plugin {
    static id = "warehouseStockOption";
    resources = {
        builder_actions: {WarehouseStockConfigAction},
    };
}

registry.category("website-plugins").add(WarehouseStockOptionPlugin.id, WarehouseStockOptionPlugin);
registry.category("website-options").add(WarehouseStockOption.id, WarehouseStockOption);
