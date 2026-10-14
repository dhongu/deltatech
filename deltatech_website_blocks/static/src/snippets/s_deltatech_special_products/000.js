/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.DeltatechSpecialProducts = publicWidget.Widget.extend({
    selector: ".s_deltatech_special_products",
    events: {
        "click .s_deltatech_special_product_toggle": "_onToggleDetails",
    },

    /**
     * @override
     */
    start() {
        if (!this.el) return this._super.apply(this, arguments);
        // In editor mode, details are always visible via CSS, but we ensure we don't interfere
        if (this.el.closest("body").classList.contains("editor_enable")) {
            return this._super.apply(this, arguments);
        }
        this.scrollTimeout = null;
        return this._super.apply(this, arguments);
    },

    destroy() {
        if (this.scrollTimeout) {
            clearTimeout(this.scrollTimeout);
        }
        this._super.apply(this, arguments);
    },

    /**
     * @private
     * @param {Event} ev
     */
    _onToggleDetails(ev) {
        const $btn = $(ev.currentTarget);
        const $item = $btn.closest(".s_deltatech_special_product_item");
        const $details = $item.find(".s_deltatech_special_product_details");
        const isActive = $item.hasClass("is-active");

        // Close all other items
        const $others = this.$(".s_deltatech_special_product_item").not($item);
        $others.removeClass("is-active");
        $others.find(".s_deltatech_special_product_details").addClass("d-none");
        this.$(".s_deltatech_special_product_toggle").not($btn).text("View Details");

        // Toggle current item
        $item.toggleClass("is-active");
        $details.toggleClass("d-none");
        $btn.text(!isActive ? "Hide Details" : "View Details");

        if (!isActive) {
            // Scroll to the item if it's not fully in view after expansion
            this.scrollTimeout = setTimeout(() => {
                if (!this.el || !document.contains(this.el)) return;
                const headerOffset = 100; // Account for potential sticky header
                const elementPosition = $item[0].getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: "smooth",
                });
                this.scrollTimeout = null;
            }, 500); // Increased delay for mobile responsiveness
        }
    },
});

export default publicWidget.registry.DeltatechSpecialProducts;
