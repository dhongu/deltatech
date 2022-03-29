odoo.define("deltatech_website_billing_addresses.billing_addresses", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");

    publicWidget.registry.websiteSaleCartBillingAdress = publicWidget.Widget.extend({
        selector: ".oe_website_sale .oe_cart",
        events: {
            "click .js_change_billing": "_onClickChangeBilling",
            "click .js_edit_billing_address": "_onClickEditBillingAddress",
        },

        // --------------------------------------------------------------------------
        // Handlers
        // --------------------------------------------------------------------------

        /**
         * @private
         * @param {Event} ev
         */
        _onClickChangeBilling: function (ev) {
            var $old = $(".all_billings").find(".card.border.border-primary");
            $old.find(".btn-bill").toggle();
            $old.addClass("js_change_billing");
            $old.removeClass("border border-primary");

            var $new = $(ev.currentTarget).parent("div.one_kanban").find(".card");
            $new.find(".btn-bill").toggle();
            $new.removeClass("js_change_billing");
            $new.addClass("border border-primary");

            var $form = $(ev.currentTarget).parent("div.one_kanban").find("form.d-none");
            $.post($form.attr("action"), $form.serialize() + "&xhr=1");
        },
        /**
         * @private
         * @param {Event} ev
         */
        _onClickEditBillingAddress: function (ev) {
            ev.preventDefault();
            $(ev.currentTarget)
                .closest("div.one_kanban")
                .find("form.d-none")
                .attr("action", "/shop/billing_address")
                .submit();
        },
    });
});
