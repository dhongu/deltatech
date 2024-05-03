odoo.define("deltatech_website_billing_addresses.billing_addresses", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");

    publicWidget.registry.websiteSaleCartBillingAddress = publicWidget.Widget.extend({
        selector: ".oe_website_sale .oe_cart",
        events: {
            "click .js_change_billing": "_onClickChangeBilling",
            "click .js_edit_billing_address": "_onClickEditBillingAddress",
            'change select[name="is_company"]': "_onChangeIsCompany",
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

        _onChangeIsCompany: function () {
            var $is_company = $('select[name="is_company"]');
            var is_company = $is_company.val() || "no";

            var $vat = $('input[name="vat"]');
            var $vat_warning = $('[t-if="vat_warning"]');
            var $company_name = $('input[name="company_name"]');
            var $name = $('input[name="name"]');

            $("#div_email").hide();
            $(".div_street2").hide();

            if (is_company === "yes") {
                $("#div_phone").hide();
                $vat.parent().show();
                $vat_warning.show();
                $company_name.parent().show();
                $name.parent().hide();
            } else {
                $("#div_phone").show();
                $vat.parent().hide();
                $vat_warning.hide();
                $company_name.parent().hide();
                $name.parent().show();
            }
        },
    });

    publicWidget.registry.websiteSaleCartBillingAddressShow = publicWidget.Widget.extend({
        selector: ".js_is_company",

        start: function () {
            var websiteSaleCartBillingAddress = new publicWidget.registry.websiteSaleCartBillingAddress();
            websiteSaleCartBillingAddress._onChangeIsCompany();
        },
    });
});
