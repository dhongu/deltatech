/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.QtyInfoPopover = publicWidget.Widget.extend({
    selector: '#product_qty_restrictions',
    
    start: function () {
        var self = this;
        // Use Bootstrap from window object (loaded by Odoo)
        var Popover = window.Popover || (window.bootstrap && window.bootstrap.Popover);
        if (Popover) {
            this.$('.qty-info-popover').each(function() {
                new Popover(this);
            });
        } else {
            // Fallback: use jQuery popover if available
            if (this.$('.qty-info-popover').popover) {
                this.$('.qty-info-popover').popover();
            }
        }
        return this._super.apply(this, arguments);
    },
});

export default publicWidget.registry.QtyInfoPopover;
