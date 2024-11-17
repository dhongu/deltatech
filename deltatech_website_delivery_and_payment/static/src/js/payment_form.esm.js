/** @odoo-module */

// import "@website_sale/js/website_sale_delivery";
import publicWidget from "@web/legacy/js/public/public_widget";

// PublicWidget.registry.websiteSaleDelivery.include({
//     start: function () {
//         this.paymentOptions = document.querySelectorAll('input[name="o_payment_radio"]');
//         return this._super.apply(this, ...arguments);
//     },
//
//     _setEnablePaymentOption(radio, enabled) {
//         const node = radio.closest('[name="o_payment_option"]');
//         if (enabled) {
//             node.classList.remove("d-none");
//             node.classList.add("list-group-item");
//         } else {
//             node.classList.add("d-none");
//             node.classList.remove("list-group-item");
//             radio.checked = false;
//         }
//     },
//
//     _onCarrierClick: function (ev) {
//         const input = ev.currentTarget.querySelector("input");
//         // Data-acquirer-allowed-ids is a comma-separated list of acquirer ids : ex: "[1,2,3]"
//         let acquirerAllowedIds = input.getAttribute("data-acquirer-allowed-ids");
//         if (acquirerAllowedIds) {
//             acquirerAllowedIds = acquirerAllowedIds.replace(/[\[\] ]/g, "").split(",");
//         }
//         for (const option of this.paymentOptions) {
//             var isEnable = true;
//             if (acquirerAllowedIds) {
//                 const acquirerId = option.dataset.providerId;
//                 isEnable = acquirerAllowedIds.includes(acquirerId);
//             }
//             this._setEnablePaymentOption(option, isEnable);
//         }
//
//         this._super(...arguments);
//     },
// });
