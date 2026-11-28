import {PosAccessRightPlugin} from "@point_of_sale/app/plugins/access_right_plugin";
import {patch} from "@web/core/utils/patch";

patch(PosAccessRightPlugin.prototype, {
    /**
     * The Price key of the numpad asks this getter, and pos_hr leaves the price mode when it
     * turns true, so locking it here closes the manual price change whatever the role.
     */
    get disablePriceButton() {
        if (this.config.restrict_price_control && this.config.lock_price_for_managers) {
            return true;
        }
        return super.disablePriceButton;
    },
});
