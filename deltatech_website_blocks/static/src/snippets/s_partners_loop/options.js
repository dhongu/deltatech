/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";

export const PartnersLoopOptions = options.Class.extend({
    /**
     * @override
     */
    cleanForSave: async function () {
        await this._super(...arguments);
        // Remove cloned nodes and their attributes
        this.$target.find('.partners-track [aria-hidden="true"]').remove();
        const $track = this.$target.find(".partners-track");
        $track.each((i, el) => {
            delete el.dataset.duplicated;
            el.style.removeProperty("transform");
            el.style.removeProperty("animation");
        });
        this.$target.removeClass("is-ready");
    },
    /**
     * @override
     */
    onBuilt: function () {
        this._super(...arguments);
        // Ensure it's clean when first dropped
        this.$target.find('.partners-track [aria-hidden="true"]').remove();
        const $track = this.$target.find(".partners-track");
        $track.each((i, el) => {
            delete el.dataset.duplicated;
            el.style.removeProperty("transform");
            el.style.removeProperty("animation");
        });
        this.$target.removeClass("is-ready");
    },

    /**
     * @override
     */
    onFocus: function () {
        this._super(...arguments);
        // Extra check to remove any clones when the snippet is focused in the editor
        this.$target.find('.partners-track [aria-hidden="true"]').remove();
    },
});

options.registry.PartnersLoopOptions = PartnersLoopOptions;

export default {
    PartnersLoopOptions,
};
