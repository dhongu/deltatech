/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget";

function debounce(fn, delay) {
    let t;
    return function (...args) {
        clearTimeout(t);
        t = setTimeout(() => fn.apply(this, args), delay);
    };
}

export const PurchasePrice = PublicWidget.Widget.extend({
    selector: ".o-purchase-price",
    init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
        this._onChange = debounce(this._onChange.bind(this), 500);
    },
    start() {
        this.el.addEventListener("change", this._onChange);
        this.el.addEventListener("input", this._onChange);
        return this._super(...arguments);
    },
    _onChange() {
        const accessToken =
            this.el.dataset.accessToken || this.el.dataset.access_token || this.el.getAttribute("data-access-token");
        const orderId = this.el.dataset.orderId || this.el.getAttribute("data-order-id");
        const lineId = this.el.dataset.lineId || this.el.getAttribute("data-line-id");
        const value = this.el.value;
        if (!orderId || !accessToken || !lineId) return;
        const payload = {};
        payload[`price_${lineId}`] = value;
        this.rpc(`/my/purchase/${orderId}/update_price_note?access_token=${accessToken}`, payload);
    },
});

export const PurchaseProductName = PublicWidget.Widget.extend({
    selector: ".o-purchase-product-name",
    init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
        this._onChange = debounce(this._onChange.bind(this), 500);
    },
    start() {
        this.el.addEventListener("change", this._onChange);
        this.el.addEventListener("input", this._onChange);
        return this._super(...arguments);
    },
    _onChange() {
        const accessToken =
            this.el.dataset.accessToken || this.el.dataset.access_token || this.el.getAttribute("data-access-token");
        const orderId = this.el.dataset.orderId || this.el.getAttribute("data-order-id");
        const lineId = this.el.dataset.lineId || this.el.getAttribute("data-line-id");
        const value = this.el.value;
        if (!orderId || !accessToken || !lineId) return;
        const payload = {};
        payload[`name_${lineId}`] = value;
        this.rpc(`/my/purchase/${orderId}/update_price_note?access_token=${accessToken}`, payload);
    },
});

PublicWidget.registry.PurchasePrice = PurchasePrice;
PublicWidget.registry.PurchaseProductName = PurchaseProductName;

export const PurchasePickup = PublicWidget.Widget.extend({
    selector: ".o-purchase-pickup",
    init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
    },
    start() {
        this.el.addEventListener("change", this._onChange.bind(this));
        return this._super(...arguments);
    },
    _onChange() {
        const accessToken =
            this.el.dataset.accessToken || this.el.dataset.access_token || this.el.getAttribute("data-access-token");
        const orderId = this.el.dataset.orderId || this.el.getAttribute("data-order-id");
        const value = this.el.value;
        if (!orderId || !accessToken || !value) return;
        const payload = { partner_pickup_address_id: value };
        this.rpc(`/my/purchase/${orderId}/update_pickup?access_token=${accessToken}`, payload);
    },
});

PublicWidget.registry.PurchasePickup = PurchasePickup;
