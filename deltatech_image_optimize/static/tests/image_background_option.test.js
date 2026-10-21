import {describe, expect, test} from "@odoo/hoot";
import {waitForNone} from "@odoo/hoot-dom";
import {contains, onRpc} from "@web/../tests/web_test_helpers";
import {defineWebsiteModels, setupWebsiteBuilder} from "@website/../tests/builder/website_helpers";

defineWebsiteModels();

const PNG =
    "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAIAQMAAAD+wSzIAAAABlBMVEX///+/v7+jQ3Y5AAAADklEQVQI12P4AIX8EAgALgAD/aNpbtEAAAAASUVORK5CYII=";

function picture(model) {
    return `
        <main>
            <div class="o_wsale_product_images">
                <div class="o_editable" contenteditable="false" data-oe-model="${model}" data-oe-id="7"
                    data-oe-field="image_1920" data-oe-type="image" data-oe-expression="product.image_1920"
                    data-oe-xpath="/t[1]/div[1]">
                    <img src="/web/static/img/logo.png" alt="Picture">
                </div>
            </div>
        </main>`;
}

function mockRoutes() {
    onRpc("/deltatech_image_optimize/bg/preview", async (request) => {
        const {params} = await request.json();
        expect.step(`preview ${params.model} ${params.res_id} ${params.method || ""}`);
        return {method: params.method || "auto", rembg: false, before: PNG, after: PNG, warning: false};
    });
    onRpc("/deltatech_image_optimize/bg/apply", async (request) => {
        const {params} = await request.json();
        expect.step(`apply ${params.model} ${params.res_id} ${params.method}`);
        return true;
    });
    onRpc("ir.ui.view", "save", () => []);
}

describe("deltatech_image_optimize", () => {
    test("product picture: preview, then apply with the chosen method", async () => {
        mockRoutes();
        await setupWebsiteBuilder(picture("product.template"));
        await contains(":iframe img[alt=Picture]").click();
        await contains("[data-action-id=dtRemoveImageBackground]").click();
        await expect.waitForSteps(["preview product.template 7 "]);
        expect(".o_dt_bg_dialog option[value=rembg]").toHaveAttribute("disabled");
        await contains(".o_dt_bg_dialog select").select("uniform");
        await expect.waitForSteps(["preview product.template 7 uniform"]);
        await contains(".o_dt_bg_apply:enabled").click();
        await expect.waitForSteps(["apply product.template 7 uniform"]);
        await waitForNone(".o_dt_bg_dialog");
    });

    test("cancel writes nothing", async () => {
        mockRoutes();
        await setupWebsiteBuilder(picture("product.image"));
        await contains(":iframe img[alt=Picture]").click();
        await contains("[data-action-id=dtRemoveImageBackground]").click();
        await expect.waitForSteps(["preview product.image 7 "]);
        await contains(".modal-footer .btn-secondary").click();
        await waitForNone(".o_dt_bg_dialog");
        expect.verifySteps([]);
    });

    test("no button on a picture that is not a product picture", async () => {
        await setupWebsiteBuilder(picture("res.partner"));
        await contains(":iframe img[alt=Picture]").click();
        await contains(".o_customize_tab [data-container-title]").click();
        expect("[data-action-id=dtRemoveImageBackground]").toHaveCount(0);
    });
});
