/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.QtyInfoPopover = publicWidget.Widget.extend({
    selector: "#product_qty_restrictions",

    start: function () {
        // Initialize popovers using Bootstrap if available
        const Popover = window.Popover || (window.bootstrap && window.bootstrap.Popover);
        if (Popover) {
            this.$(".qty-info-popover").each(function () {
                /* eslint-disable no-new */
                new Popover(this);
                /* eslint-enable no-new */
            });
        } else if (this.$(".qty-info-popover").popover) {
            // Fallback: use jQuery popover if available
            this.$(".qty-info-popover").popover();
        }
        return this._super.apply(this, arguments);
    },
});

export default publicWidget.registry.QtyInfoPopover;
