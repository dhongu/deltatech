/** @odoo-module */

import WebsiteSaleCheckout from "@website_sale/js/checkout";

WebsiteSaleCheckout.include({
    /**
     * @override
     */
    async start() {
        await this._super(...arguments);
        const checkedRadio = this.el.querySelector('input[name="o_delivery_radio"]:checked');
        if (checkedRadio) {
            this._updatePaymentOptions(checkedRadio);
        }
    },

    /**
     * @override
     */
    async _selectDeliveryMethod(ev) {
        await this._super(...arguments);
        this._updatePaymentOptions(ev.currentTarget);
    },

    /**
     * Update the payment options visibility based on the selected delivery carrier.
     *
     * @private
     * @param {HTMLInputElement} deliveryRadio
     * @returns {void}
     */
    _updatePaymentOptions(deliveryRadio) {
        let acquirerAllowedIds = deliveryRadio.getAttribute("data-acquirer-allowed-ids");
        if (acquirerAllowedIds) {
            acquirerAllowedIds = JSON.parse(acquirerAllowedIds);
        }

        const paymentOptions = document.querySelectorAll('input[name="o_payment_radio"]');
        for (const option of paymentOptions) {
            let isVisible = true;
            if (acquirerAllowedIds && acquirerAllowedIds.length > 0) {
                const providerId = parseInt(option.dataset.providerId, 10);
                isVisible = acquirerAllowedIds.includes(providerId);
            }
            this._setPaymentOptionVisibility(option, isVisible);
        }
    },

    /**
     * Show or hide a payment option.
     *
     * @private
     * @param {HTMLInputElement} radio
     * @param {Boolean} visible
     * @returns {void}
     */
    _setPaymentOptionVisibility(radio, visible) {
        const container = radio.closest('[name="o_payment_option"]');
        if (container) {
            if (visible) {
                container.classList.remove("d-none");
            } else {
                container.classList.add("d-none");
                if (radio.checked) {
                    radio.checked = false;
                    // Trigger change to let other scripts know it's unchecked if needed
                    radio.dispatchEvent(new Event("change", {bubbles: true}));
                }
            }
        }
    },
});
