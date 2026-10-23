import {Navbar} from "@point_of_sale/app/components/navbar/navbar";
import {patch} from "@web/core/utils/patch";

patch(Navbar.prototype, {
    // Pos_hr keeps Close Register for managers; only this button moves to the cashier.
    get showCloseSession() {
        return super.showCloseSession || this.pos.cashierCanCloseRegister();
    },
});
