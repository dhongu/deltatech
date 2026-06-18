import {registry} from "@web/core/registry";
import {Interaction} from "@web/public/interaction";

export class QuantityInfoPopover extends Interaction {
    static selector = "#product_qty_restrictions";

    setup() {
        this.el.querySelectorAll(".qty-info-popover").forEach((el) => {
            const popover = window.Popover.getOrCreateInstance(el);
            this.registerCleanup(() => popover.dispose());
        });
    }
}

registry
    .category("public.interactions")
    .add("deltatech_sale_multiple_website.quantity_info_popover", QuantityInfoPopover);
