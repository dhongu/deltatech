/** @odoo-module */

import "@website_sale/js/website_sale_delivery";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.websiteSaleDelivery.include({
    start: function () {
        this.paymentOptions = document.querySelectorAll('input[name="o_payment_radio"]');
        return this._super.apply(this, ...arguments);
    },

    _setEnablePaymentOption(radio, enabled) {
        const node = radio.closest('[name="o_payment_option"]');
        if (enabled) {
            node.classList.remove("d-none");
            node.classList.add("list-group-item");
        } else {
            node.classList.add("d-none");
            node.classList.remove("list-group-item");
            radio.checked = false;
        }
    },

    _onCarrierClick: function (ev) {
        const input = ev.currentTarget.querySelector("input");
        let acquirerAllowedIds = input.getAttribute("data-acquirer-allowed-ids");
        acquirerAllowedIds = JSON.parse(acquirerAllowedIds);

        let  isEnable = true;
        for (let option of this.paymentOptions) {
            const acquirerId = JSON.parse(option.dataset.providerId);
            isEnable = true;
            if (acquirerAllowedIds) {
                 isEnable = acquirerAllowedIds.includes(acquirerId);
            }
            this._setEnablePaymentOption(option, isEnable);
        }

        this._super(...arguments);
    },
});
