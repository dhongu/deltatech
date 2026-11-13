import {Navbar} from "@point_of_sale/app/components/navbar/navbar";
import {StockOpsDialog} from "./stock_ops_dialog.esm";
import {patch} from "@web/core/utils/patch";

patch(Navbar.prototype, {
    openStockOps(operationType) {
        this.dialog.add(StockOpsDialog, {operationType});
    },
});
