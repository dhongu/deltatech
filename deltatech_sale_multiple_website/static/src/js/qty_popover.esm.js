import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {formatFloat} from "@web/core/utils/numbers";
import {patch} from "@web/core/utils/patch";
import {Interaction} from "@web/public/interaction";
import {WebsiteSale} from "@website_sale/interactions/website_sale";

function refreshPopover(button, title, content) {
    window.Popover?.getInstance(button)?.dispose();
    button.setAttribute("title", title);
    button.setAttribute("aria-label", title);
    button.setAttribute("data-bs-content", content);
    window.Popover?.getOrCreateInstance(button);
}

patch(WebsiteSale.prototype, {
    _onChangeCombination(ev, parent, combination) {
        super._onChangeCombination(...arguments);

        const restrictions = parent.querySelector("#product_qty_restrictions");
        if (!restrictions) {
            return;
        }

        const precision = combination.sale_qty_precision ?? 2;
        const minimum = combination.sale_qty_minimum || 0;
        const multiple = combination.sale_qty_multiple || 0;
        const formatQuantity = (quantity) => formatFloat(quantity, {digits: [false, precision], trailingZeros: false});

        const minimumRule = restrictions.querySelector(".qty-minimum-rule");
        minimumRule.classList.toggle("d-none", !minimum);
        if (minimum) {
            const formattedMinimum = formatQuantity(minimum);
            minimumRule.querySelector(".qty-rule-value").textContent = formattedMinimum;
            refreshPopover(
                minimumRule.querySelector(".qty-info-popover"),
                _t("Minimum quantity"),
                _t("The minimum order quantity is %s units.", formattedMinimum)
            );
        }

        const multipleRule = restrictions.querySelector(".qty-multiple-rule");
        multipleRule.classList.toggle("d-none", !multiple);
        if (multiple) {
            const formattedMultiple = formatQuantity(multiple);
            multipleRule.querySelector(".qty-rule-value").textContent = formattedMultiple;
            refreshPopover(
                multipleRule.querySelector(".qty-info-popover"),
                _t("Quantity multiple"),
                _t(
                    "Quantity must be a multiple of %s (e.g. %s, %s, %s...).",
                    formattedMultiple,
                    formattedMultiple,
                    formatQuantity(multiple * 2),
                    formatQuantity(multiple * 3)
                )
            );
        }

        restrictions.classList.toggle("d-none", !minimum && !multiple);
    },
});

export class QuantityInfoPopover extends Interaction {
    static selector = "#product_qty_restrictions";

    setup() {
        this.el.querySelectorAll(".qty-info-popover").forEach((element) => {
            const popover = window.Popover.getOrCreateInstance(element);
            this.registerCleanup(() => popover.dispose());
        });
    }
}

registry
    .category("public.interactions")
    .add("deltatech_sale_multiple_website.quantity_info_popover", QuantityInfoPopover);
