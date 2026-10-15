import * as Chrome from "@point_of_sale/../tests/pos/tours/utils/chrome_util";
import * as Dialog from "@point_of_sale/../tests/generic_helpers/dialog_util";
import * as Order from "@point_of_sale/../tests/generic_helpers/order_widget_util";
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
            // POSEXTRA-003: the deposit line was removed by hand; the next
            // water merges into the existing line (3 bottles), so the new
            // deposit line is for 3 bottles, not for the 1 just requested.
            ProductScreen.clickOrderline("Bottle Deposit", "4"),
            ProductScreen.clickNumpad("⌫"),
            ProductScreen.selectedOrderlineHas("Bottle Deposit", "0"),
            ProductScreen.clickNumpad("⌫"),
            Order.doesNotHaveLine({productName: "Bottle Deposit"}),
            ProductScreen.checkOrderlinesNumber(1),
            ProductScreen.clickDisplayedProduct("Bottled Water"),
            ProductScreen.orderLineHas("Bottled Water", "3"),
            ProductScreen.orderLineHas("Bottle Deposit", "6"),
            ProductScreen.checkOrderlinesNumber(2),
            // POSEXTRA-002: removing the main line removes its deposit too
            // (the first backspace sets it to 0, the second deletes it).
            ProductScreen.clickOrderline("Bottled Water", "3"),
            ProductScreen.clickNumpad("⌫"),
            ProductScreen.selectedOrderlineHas("Bottled Water", "0"),
            ProductScreen.clickNumpad("⌫"),
            ProductScreen.orderIsEmpty(),
        ].flat(),
});

// POSEXTRA-001: cancelling the configurator of a product with an extra
// product adds neither the product nor its extra line.
registry.category("web_tour.tours").add("DeltatechExtraLinePosCancelTour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),
            ProductScreen.clickDisplayedProduct("Configurable Chair"),
            Dialog.cancel(),
            ProductScreen.orderIsEmpty(),
        ].flat(),
});

// POSEXTRA-003: in a return preset the water line is -1, so the first
// deposit line is -2, not +2 taken from the requested quantity.
registry.category("web_tour.tours").add("DeltatechExtraLinePosReturnTour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),
            ProductScreen.clickDisplayedProduct("Bottled Water"),
            ProductScreen.orderLineHas("Bottled Water", "-1"),
            ProductScreen.orderLineHas("Bottle Deposit", "-2"),
            ProductScreen.checkOrderlinesNumber(2),
        ].flat(),
});
