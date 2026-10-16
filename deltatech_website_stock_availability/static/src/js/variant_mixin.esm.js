import {ProductPage} from "@website_sale/interactions/product_page";
import {patch} from "@web/core/utils/patch";
import {renderToFragment} from "@web/core/utils/render";

patch(ProductPage.prototype, {
    async _onChangeCombination(ev, parent, combination) {
        // In 20.0 the core method is async (it awaits the cart quantity before
        // adjusting `free_qty`): render the lead time messages after it.
        await super._onChangeCombination(...arguments);
        this._onChangeLeadTimeMessage(ev, parent, combination);
    },

    _onChangeLeadTimeMessage(ev, parent, combination) {
        if (!combination.product_id) {
            return;
        }
        // 20.0: the `.product_id` input and `.js_main_product` class are gone; the
        // selected variant is kept on the add to cart button (`data-product-id`),
        // updated by the core `_onChangeCombination` before we get here.
        const addToCart = parent.querySelector('button[name="add_to_cart"]');
        const productId = parseInt(addToCart?.dataset.productId || 0, 10);
        if (productId && combination.product_id !== productId) {
            return;
        }

        const addQtyInput = parent.querySelector('input[name="add_qty"]');
        combination.selected_qty = addQtyInput ? addQtyInput.value : 1;

        const container = parent.closest(".oe_website_sale") || this.el;
        const product_template_id = combination.product_template_id || combination.product_template;

        const leadTimeAvailabilityClass = ".lead_time_availability_" + product_template_id;
        container.querySelectorAll(leadTimeAvailabilityClass).forEach((el) => el.remove());

        const leadTimeMessagesContainer = container.querySelector("div.lead_time_messages");
        if (leadTimeMessagesContainer) {
            leadTimeMessagesContainer.replaceChildren(
                renderToFragment("deltatech_website_stock_availability.lead_time_availability", combination)
            );
        }

        const leadTimeIntervalClass = ".lead_time_interval_" + product_template_id;
        container.querySelectorAll(leadTimeIntervalClass).forEach((el) => el.remove());

        const leadTimeMessagesIntervalContainer = container.querySelector("div.lead_time_messages_interval");
        if (leadTimeMessagesIntervalContainer) {
            leadTimeMessagesIntervalContainer.replaceChildren(
                renderToFragment("deltatech_website_stock_availability.lead_time_interval", combination)
            );
        }
    },
});
