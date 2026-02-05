import {WebsiteSale} from "@website_sale/interactions/website_sale";
import {patch} from "@web/core/utils/patch";
import {renderToFragment} from "@web/core/utils/render";

patch(WebsiteSale.prototype, {
    _onChangeCombination() {
        super._onChangeCombination(...arguments);
        this._onChangeLeadTimeMessage(...arguments);
    },

    _onChangeLeadTimeMessage(ev, $parent, combination) {
        let product_id = 0;
        // Needed for list view of variants
        if ($parent.querySelector("input.product_id:checked")) {
            product_id = $parent.querySelector("input.product_id:checked").value;
        } else if ($parent.querySelector(".product_id")) {
            product_id = $parent.querySelector(".product_id").value;
        }

        const isMainProduct =
            combination.product_id &&
            ($parent.classList.contains("js_main_product") ||
                $parent.classList.contains("main_product") ||
                $parent.closest(".js_main_product")) &&
            combination.product_id === parseInt(product_id, 10);

        if (!isMainProduct) {
            return;
        }

        const $addQtyInput = $parent.querySelector('input[name="add_qty"]');
        const qty = $addQtyInput ? $addQtyInput.value : 1;
        combination.selected_qty = qty;

        const $container = $parent.closest(".oe_website_sale");
        if (!$container) {
            return;
        }

        const product_template_id = combination.product_template_id || combination.product_template;

        const leadTimeAvailabilityClass = ".lead_time_availability_" + product_template_id;
        $container.querySelectorAll(leadTimeAvailabilityClass).forEach((el) => el.remove());

        const $availabilityMessage = renderToFragment(
            "deltatech_website_stock_availability.lead_time_availability",
            combination
        );
        const leadTimeMessagesContainer = $container.querySelector("div.lead_time_messages");
        if (leadTimeMessagesContainer) {
            leadTimeMessagesContainer.innerHTML = "";
            leadTimeMessagesContainer.appendChild($availabilityMessage);
        }

        const leadTimeIntervalClass = ".lead_time_interval_" + product_template_id;
        $container.querySelectorAll(leadTimeIntervalClass).forEach((el) => el.remove());

        const $intervalMessage = renderToFragment(
            "deltatech_website_stock_availability.lead_time_interval",
            combination
        );
        const leadTimeMessagesIntervalContainer = $container.querySelector("div.lead_time_messages_interval");
        if (leadTimeMessagesIntervalContainer) {
            leadTimeMessagesIntervalContainer.innerHTML = "";
            leadTimeMessagesIntervalContainer.appendChild($intervalMessage);
        }
    },
});
