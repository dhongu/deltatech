/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Fill collapsed sidebar branches on first expand.
 *
 * The listing page renders only the open branch of the category tree; every
 * collapsed `<ul>` arrives empty with a `data-lazy-category` id. Bootstrap's
 * `show.bs.collapse` bubbles, so one listener on the container also covers
 * branches injected by an earlier expand.
 */
publicWidget.registry.deltatechLazyCategories = publicWidget.Widget.extend({
    selector: ".products_categories, .wsale_products_categories_list",

    /**
     * @override
     */
    start() {
        this._onShown = this._onShown.bind(this);
        this.el.addEventListener("show.bs.collapse", this._onShown);
        return this._super.apply(this, arguments);
    },

    /**
     * @override
     */
    destroy() {
        this.el.removeEventListener("show.bs.collapse", this._onShown);
        this._super.apply(this, arguments);
    },

    /**
     * @private
     * @param {Event} ev
     */
    async _onShown(ev) {
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
        const activeCategory = this._activeCategoryId();
        if (activeCategory) {
            params.set("active_category", activeCategory);
        }
        const query = params.toString();
        const url = `/shop/category_children/${encodeURIComponent(categoryId)}${query ? `?${query}` : ""}`;

        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            list.innerHTML = await response.text();
        } catch {
            // Leave the branch empty rather than breaking the page; clearing the
            // flag lets the next expand try again.
            delete list.dataset.lazyLoaded;
        }
    },

    /**
     * Id of the category the page is currently showing, if any.
     *
     * @private
     * @returns {String} empty when the page is the unfiltered shop
     */
    _activeCategoryId() {
        const fromQuery = new URLSearchParams(window.location.search).get("category");
        if (fromQuery) {
            return fromQuery;
        }
        // /shop/category/<slug>-<id> — the id is the trailing number of the slug.
        const match = window.location.pathname.match(/\/shop\/category\/.*?(\d+)\/?$/);
        return match ? match[1] : "";
    },
});
