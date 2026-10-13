import * as Chrome from "@point_of_sale/../tests/pos/tours/utils/chrome_util";
import * as Dialog from "@point_of_sale/../tests/generic_helpers/dialog_util";
import * as ProductScreen from "@point_of_sale/../tests/pos/tours/utils/product_screen_util";
import {registry} from "@web/core/registry";

// "Bottled Water" adds "Bottle Deposit" with extra_qty = 2: the deposit line
// follows the water quantity, and stays a single line.
registry.category("web_tour.tours").add("DeltatechExtraLinePosTour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),
            ProductScreen.clickDisplayedProduct("Bottled Water"),
            ProductScreen.orderLineHas("Bottled Water", "1"),
            ProductScreen.orderLineHas("Bottle Deposit", "2"),
            ProductScreen.clickDisplayedProduct("Bottled Water"),
            ProductScreen.orderLineHas("Bottled Water", "2"),
            ProductScreen.orderLineHas("Bottle Deposit", "4"),
            ProductScreen.checkOrderlinesNumber(2),
        ].flat(),
});
