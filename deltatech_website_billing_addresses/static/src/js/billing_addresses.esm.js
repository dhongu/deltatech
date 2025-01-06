/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

class WebsiteSaleCartBillingAddress extends publicWidget.Widget {
    selector = ".oe_website_sale .oe_cart";
    events = {
        "click .js_change_billing": this._onClickChangeBilling,
        "click .js_edit_billing_address": this._onClickEditBillingAddress,
        'change select[name="is_company"]': this._onChangeIsCompany,
    };

    _onClickChangeBilling(ev) {
        const $old = $(".all_billings").find(".card.border.border-primary");
        $old.find(".btn-bill").toggle();
        $old.addClass("js_change_billing");
        $old.removeClass("border border-primary");

        const $new = $(ev.currentTarget).parent("div.one_kanban").find(".card");
        $new.find(".btn-bill").toggle();
        $new.removeClass("js_change_billing");
        $new.addClass("border border-primary");

        const $form = $(ev.currentTarget).parent("div.one_kanban").find("form.d-none");
        $.post($form.attr("action"), $form.serialize() + "&xhr=1");
    }

    _onClickEditBillingAddress(ev) {
        ev.preventDefault();
        $(ev.currentTarget)
            .closest("div.one_kanban")
            .find("form.d-none")
            .attr("action", "/shop/billing_address")
            .submit();
    }

    _onChangeIsCompany() {
        const $is_company = $('select[name="is_company"]');
        const is_company = $is_company.val() || "no";

        const $vat = $('input[name="vat"]');
        const $vat_warning = $('[t-if="vat_warning"]');
        const $company_name = $('input[name="company_name"]');
        const $name = $('input[name="name"]');

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
    }
}

class WebsiteSaleCartBillingAddressShow extends publicWidget.Widget {
    selector = ".js_is_company";

    start() {
        const websiteSaleCartBillingAddress = new WebsiteSaleCartBillingAddress();
        websiteSaleCartBillingAddress._onChangeIsCompany();
    }
}

export {WebsiteSaleCartBillingAddress, WebsiteSaleCartBillingAddressShow};
