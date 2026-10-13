import {Interaction} from "@web/public/interaction";
import {registry} from "@web/core/registry";

const STORAGE_KEY = "deltatech_wsale_attribute_filter_state";

/**
 * Selecting an attribute filter triggers a full page redirect (core
 * WebsiteSale.onChangeAttribute), which resets the open/closed state of the
 * attribute accordions and closes the mobile filters offcanvas. This
 * interaction saves that state right before the redirect and restores it on
 * the next page load, so the customer does not have to reopen the filters
 * after every selection.
 */
export class AttributeFilterState extends Interaction {
    static selector = ".oe_website_sale";

    start() {
        // Capture phase: runs before the core bubble-phase change handler
        // that redirects the page.
        this.addListener(
            this.el,
            "change",
            (ev) => {
                if (ev.target.closest("form.js_attributes, #o_wsale_price_range_option")) {
                    this.saveState();
                }
            },
            {capture: true}
        );
        this.restoreState();
    }

    /**
     * The same attribute is rendered twice: in the desktop sidebar
     * (o_products_attributes_<id>) and in the mobile offcanvas
     * (o_wsale_offcanvas_attribute_<id>). Share the saved state between the
     * two renderings by keying on the attribute id.
     */
    normalizeId(id) {
        const m = id.match(/^(?:o_products_attributes|o_wsale_offcanvas_attribute)_(\d+)$/);
        return m ? `attr-${m[1]}` : id;
    }

    saveState() {
        const expanded = [...document.querySelectorAll("form.js_attributes .accordion-collapse.show")]
            .filter((el) => el.id)
            .map((el) => this.normalizeId(el.id));
        const offcanvas = document.getElementById("o_wsale_offcanvas");
        const state = {
            expanded,
            offcanvasOpen: Boolean(offcanvas && offcanvas.classList.contains("show")),
            scrollY: Math.round(window.scrollY),
        };
        try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } catch {
            // SessionStorage unavailable: lose the state, keep the navigation
        }
    }

    restoreState() {
        let state = null;
        try {
            const raw = sessionStorage.getItem(STORAGE_KEY);
            if (!raw) {
                return;
            }
            sessionStorage.removeItem(STORAGE_KEY);
            state = JSON.parse(raw);
        } catch {
            return;
        }
        if (!state || !Array.isArray(state.expanded)) {
            return;
        }
        const expanded = new Set(state.expanded);

        // Desktop sidebar ("Collapsed Attributes & Variants filters" option):
        // apply the saved collapse state directly.
        for (const collapseEl of document.querySelectorAll("form.js_attributes .accordion-collapse")) {
            if (!collapseEl.id || collapseEl.closest("#o_wsale_offcanvas")) {
                continue;
            }
            this.applyCollapseState(collapseEl, expanded.has(this.normalizeId(collapseEl.id)));
        }

        this.restoreOffcanvasState(expanded, state.offcanvasOpen);

        if (state.scrollY) {
            window.scrollTo({top: state.scrollY, behavior: "instant"});
        }
    }

    restoreOffcanvasState(expanded, reopen) {
        const offcanvas = document.getElementById("o_wsale_offcanvas");
        if (!offcanvas) {
            return;
        }
        // The core OffCanvas interaction folds/unfolds every section based on
        // its button's data-status each time the offcanvas is shown or hidden.
        // Rewrite data-status so that mechanism reproduces the saved state
        // instead of resetting it.
        for (const btn of offcanvas.querySelectorAll("button[data-status]")) {
            const targetId = (btn.dataset.bsTarget || "").replace(/^#/, "");
            if (targetId) {
                btn.dataset.status = expanded.has(this.normalizeId(targetId)) ? "active" : "inactive";
            }
        }
        if (reopen && window.Offcanvas) {
            window.Offcanvas.getOrCreateInstance(offcanvas).show();
        }
    }

    applyCollapseState(collapseEl, shouldShow) {
        collapseEl.classList.toggle("show", shouldShow);
        const btn = document.querySelector(`[data-bs-target="#${collapseEl.id}"]`);
        if (btn) {
            btn.classList.toggle("collapsed", !shouldShow);
            btn.setAttribute("aria-expanded", shouldShow ? "true" : "false");
        }
    }
}

registry
    .category("public.interactions")
    .add("deltatech_website_sale_attribute_filter.attribute_filter_state", AttributeFilterState);
