import {PosStore} from "@point_of_sale/app/services/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosStore.prototype, {
    /**
     * Employees with basic rights (pos_hr role "cashier") may close the register when
     * the register allows it. Minimal rights never do.
     */
    cashierCanCloseRegister() {
        return Boolean(
            this.config.module_pos_hr && this.config.cashier_can_close && this.getCashier()?._role === "cashier"
        );
    },
});
