import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

/**
 * Fill collapsed sidebar branches on first expand.
 *
 * The listing page renders only the open branch of the category tree; every
 * collapsed `<ul>` arrives empty with a `data-lazy-category` id. Bootstrap's
 * `show.bs.collapse` bubbles, so one listener on the container also covers
 * branches injected by an earlier expand.
 */
export class DeltatechLazyCategories extends Interaction {
    static selector = ".products_categories, .wsale_products_categories_list";

    dynamicContent = {
        _root: {
            "t-on-show.bs.collapse": this.onBranchShown,
        },
    };

    /**
     * @param {Event} ev
     */
    async onBranchShown(ev) {
        const list = ev.target;
        const categoryId = list.dataset.lazyCategory;
        // `lazyLoaded` guards against a second fetch when the visitor collapses
        // and re-expands the same branch.
        if (!categoryId || list.dataset.lazyLoaded) {
            return;
        }
        list.dataset.lazyLoaded = "1";

        // Carry the listing page's own filters over, so the fetched links keep
        // the current sort/price state like the server-rendered ones do.
        const params = new URLSearchParams(window.location.search);
        params.delete("category");
        const activeCategory = this.getActiveCategoryId();
        if (activeCategory) {
            params.set("active_category", activeCategory);
        }
        const query = params.toString();
        const url = `/shop/category_children/${encodeURIComponent(categoryId)}${query ? `?${query}` : ""}`;

        try {
            const response = await this.waitFor(fetch(url));
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            list.innerHTML = await this.waitFor(response.text());
        } catch {
            // Leave the branch empty rather than breaking the page; clearing the
            // flag lets the next expand try again.
            delete list.dataset.lazyLoaded;
        }
    }

    /**
     * Id of the category the page is currently showing, if any.
     *
     * @returns {String} empty when the page is the unfiltered shop
     */
    getActiveCategoryId() {
        const fromQuery = new URLSearchParams(window.location.search).get("category");
        if (fromQuery) {
            return fromQuery;
        }
        // /shop/category/<slug>-<id> — the id is the trailing number of the slug.
        const match = window.location.pathname.match(/\/shop\/category\/.*?(\d+)\/?$/);
        return match ? match[1] : "";
    }
}

registry
    .category("public.interactions")
    .add("deltatech_website_category.lazy_categories", DeltatechLazyCategories);
