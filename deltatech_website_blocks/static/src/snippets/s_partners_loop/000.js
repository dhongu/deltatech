/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PartnersLoop = publicWidget.Widget.extend({
    selector: ".js-partners-loop",
    events: {
        "click .partners-nav.prev": "_onPrevClick",
        "click .partners-nav.next": "_onNextClick",
    },

    /**
     * @override
     */
    start: function () {
        this.currentPosition = 0;
        this.initPartnersLoop();
        return this._super.apply(this, arguments);
    },

    initPartnersLoop: function () {
        const section = this.el;
        if (!section) return;
        const container = section.querySelector(".partners-container");
        const track = section.querySelector(".partners-track");
        if (!track || !container) return;

        // Check if we are in edit mode
        const isEditMode =
            !!document.querySelector("#oe_snippets") ||
            document.body.classList.contains("editor_enable") ||
            section.closest(".o_editable_auto_status") ||
            !!section.closest(".o_we_website_top_menu");

        // Always clean up first
        section.classList.remove("is-ready");
        track.querySelectorAll('[aria-hidden="true"]').forEach((el) => el.remove());
        delete track.dataset.duplicated;
        track.style.removeProperty("animation");
        track.style.removeProperty("transform");

        if (isEditMode) {
            // In edit mode, we want to make sure no clones exist and no animation is running.
            // We already did the cleanup above.
            // Additionally, we want to make sure the track doesn't have clones even if they were just added
            // by some other instance or saved by mistake.
            return;
        }

        const items = Array.from(track.children);
        if (items.length === 0) return;

        // We use a small timeout to ensure layout is calculated, especially for the width
        this.initTimeout = setTimeout(() => {
            if (!this.el) return;
            const container = this.el.querySelector(".partners-container");
            const track = this.el.querySelector(".partners-track");
            if (!container || !track) return;
            const containerWidth = container.offsetWidth;

            // Loop Mode
            items.forEach(function (item) {
                const clone = item.cloneNode(true);
                clone.setAttribute("aria-hidden", "true");
                track.appendChild(clone);
            });
            track.dataset.duplicated = "true";

            // Force a reflow to ensure the browser has updated the scrollWidth
            const trackWidth = track.scrollWidth;

            requestAnimationFrame(() => {
                section.classList.add("is-ready");

                // If items fit in the container (after duplication), check if we still want animation
                if (trackWidth <= containerWidth) {
                    track.style.setProperty("animation", "none", "important");
                }
            });
        }, 100);
    },

    destroy: function () {
        if (this.initTimeout) {
            clearTimeout(this.initTimeout);
        }
        this._super.apply(this, arguments);
    },

    _updateNavButtons: function () {
        const container = this.el.querySelector(".partners-container");
        const track = this.el.querySelector(".partners-track");
        const prevBtn = this.el.querySelector(".partners-nav.prev");
        const nextBtn = this.el.querySelector(".partners-nav.next");

        if (!container || !track || !prevBtn || !nextBtn) return;

        const containerWidth = container.offsetWidth;
        const trackWidth = track.scrollWidth;

        if (trackWidth > containerWidth) {
            prevBtn.classList.remove("d-none");
            nextBtn.classList.remove("d-none");
        } else {
            prevBtn.classList.add("d-none");
            nextBtn.classList.add("d-none");
        }
    },

    _onPrevClick: function (ev) {
        if (document.body.classList.contains("editor_enable")) return;
        ev.preventDefault();
        const container = this.el.querySelector(".partners-container");
        const track = this.el.querySelector(".partners-track");
        const step = 220; // Width of partner-item

        this.currentPosition += step;
        if (this.currentPosition > 0) {
            this.currentPosition = 0;
        }
        track.style.setProperty("transform", `translateX(${this.currentPosition}px)`, "important");
    },

    _onNextClick: function (ev) {
        if (document.body.classList.contains("editor_enable")) return;
        ev.preventDefault();
        const container = this.el.querySelector(".partners-container");
        const track = this.el.querySelector(".partners-track");
        const step = 220;
        const containerWidth = container.offsetWidth;
        const trackWidth = track.scrollWidth;

        this.currentPosition -= step;
        if (Math.abs(this.currentPosition) > trackWidth - containerWidth) {
            this.currentPosition = -(trackWidth - containerWidth);
        }
        track.style.setProperty("transform", `translateX(${this.currentPosition}px)`, "important");
    },
});

export default publicWidget.registry.PartnersLoop;
