/** @odoo-module **/

import {PosStore} from "@point_of_sale/app/services/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async processServerData() {
        await super.processServerData(...arguments);
        this.data.connectWebSocket("STOCK_SYNCHRONISATION", this._onStockSynchronisation.bind(this));
    },

    // Pornit din stock.quant (deltatech_pos_stock/models/stock_quant.py) de fiecare dată
    // când se schimbă stocul fizic al unui produs vândut în POS. Fără asta, `qty_available`
    // (câmp calculat, nestocat) rămâne blocat la valoarea cache-uită la deschiderea sesiunii,
    // pentru că sincronizarea normală a POS-ului filtrează pe write_date, iar acesta nu se
    // schimbă niciodată printr-o mișcare de stoc.
    _onStockSynchronisation(data) {
        const records = data && data["product.template"];
        if (records && records.length) {
            this.models.connectNewData({"product.template": records});
        }
    },
});
