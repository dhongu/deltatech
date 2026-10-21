import {clickOnEditAndWaitEditMode, registerWebsitePreviewTour} from "@website/js/tours/tour_utils";

registerWebsitePreviewTour("deltatech_image_optimize_remove_background_editor", {}, () => [
    {
        content: "Check that the product page is loaded",
        trigger: ":iframe .o_wsale_product_page",
    },
    ...clickOnEditAndWaitEditMode(),
    {
        content: "Click on the product picture",
        trigger: ":iframe #o-carousel-product .o_product_detail_img_wrapper img",
        run: "click",
    },
    {
        content: "Check that the options of the picture are loaded",
        trigger: ".o_customize_tab [data-container-title='Image']",
    },
    {
        content: "Remove the background",
        trigger: ".o_customize_tab button[data-action-id='dtRemoveImageBackground']",
        run: "click",
    },
    {
        content: "The preview is shown",
        trigger: ".o_dt_bg_dialog img.o_dt_bg_after",
    },
    {
        content: "Apply",
        trigger: ".modal .o_dt_bg_apply:enabled",
        run: "click",
    },
    {
        content: "The dialog is closed and the page reloaded in edit mode",
        trigger: "body:not(:has(.o_dt_bg_dialog)) :iframe .o_wsale_product_page",
    },
    {
        content: "The editor is unblocked",
        trigger: "body:not(:has(.o_blockUI))",
    },
]);
