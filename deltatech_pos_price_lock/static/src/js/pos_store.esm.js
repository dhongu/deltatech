import {PosStore} from "@point_of_sale/app/services/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosStore.prototype, {
    /**
     * The Price key of the numpad and the price check of pos_hr both ask this method,
     * so refusing here closes every manual price change, whatever the role of the cashier.
     */
    cashierHasPriceControlRights() {
        if (this.config.restrict_price_control && this.config.lock_price_for_managers) {
            return false;
        }
        return super.cashierHasPriceControlRights(...arguments);
    },
});
