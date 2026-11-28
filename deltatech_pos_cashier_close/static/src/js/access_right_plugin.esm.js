import {PosAccessRightPlugin} from "@point_of_sale/app/plugins/access_right_plugin";
import {patch} from "@web/core/utils/patch";

patch(PosAccessRightPlugin.prototype, {
    /**
     * Pos_hr keeps Close Register for the managers; only this right moves to the employees with
     * the Cashier role, when the register allows it. The other roles never get it from here.
     */
    get canCloseSession() {
        return super.canCloseSession || this.cashierCanCloseRegister;
    },

    get cashierCanCloseRegister() {
        return Boolean(this.config.module_pos_hr && this.config.cashier_can_close && this.cashier?._role === "cashier");
    },
});
