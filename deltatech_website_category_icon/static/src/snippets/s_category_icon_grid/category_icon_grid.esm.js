import {Interaction} from "@web/public/interaction";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";

/**
 * Fills the snippet Category Icon Grid with the categories rendered by the server.
 * The page only keeps the options; the items are fetched on each visit and removed
 * before the editor saves the page.
 */
export class CategoryIconGrid extends Interaction {
    static selector = ".s_category_icon_grid";
    dynamicContent = {
        ".s_category_icon_grid_empty": {
            "t-att-class": () => ({"d-none": Boolean(this.html)}),
        },
    };

    setup() {
        this.html = "";
        this.itemsEl = this.el.querySelector(".s_category_icon_grid_items");
    }

    async willStart() {
        const dataset = this.el.dataset;
        let categoryIds = [];
        if (dataset.mode === "manual") {
            categoryIds = JSON.parse(dataset.categoryIds || "[]").map((category) => category.id);
            if (!categoryIds.length) {
                return;
            }
        }
        this.html = await this.waitFor(
            rpc("/website/snippet/category_icon_grid", {
                category_ids: categoryIds,
                limit: parseInt(dataset.limit, 10) || 12,
            })
        );
    }

    start() {
        const template = document.createElement("template");
        template.innerHTML = this.html;
        this.itemsEl.replaceChildren(template.content);
    }

    destroy() {
        this.itemsEl.replaceChildren();
    }
}

registry.category("public.interactions").add("deltatech_website_category_icon.category_icon_grid", CategoryIconGrid);

registry.category("public.interactions.edit").add("deltatech_website_category_icon.category_icon_grid", {
    Interaction: CategoryIconGrid,
});
