/** @odoo-module **/

import {PosStore} from "@point_of_sale/app/services/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async processServerData() {
        await super.processServerData(...arguments);
        this.data.connectWebSocket("PRICE_SYNCHRONISATION", this._onPriceSynchronisation.bind(this));
    },

    // Pornit din product.template (deltatech_pos_price_sync/models/product_template.py) de
    // fiecare dată când se schimbă list_price/standard_price. write_date-ul șablonului chiar
    // se schimbă, dar cât timp sesiunea POS rămâne deschisă loadInitialData() nu mai declanșează
    // niciun RPC (vezi data_service.js), deci F5 nu ajută — trebuie împins explicit pe bus.
    _onPriceSynchronisation(data) {
        const records = data && data["product.template"];
        if (records && records.length) {
            this.models.connectNewData({"product.template": records});
        }
    },
});
