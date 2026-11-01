/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";

options.registry.PartnersLoopOptions = options.Class.extend({

    async cleanForSave() {
        await this._super(...arguments);
        this.$target.find('.partners-track [aria-hidden="true"]').remove();
        const track = this.$target.find(".partners-track")[0];
        if (track) {
            delete track.dataset.duplicated;
            track.style.removeProperty("transform");
            track.style.removeProperty("animation");
        }
        this.$target[0].classList.remove("is-ready");
    },

    onBuilt() {
        this._super(...arguments);
        this.$target.find('.partners-track [aria-hidden="true"]').remove();
        const track = this.$target.find(".partners-track")[0];
        if (track) {
            delete track.dataset.duplicated;
            track.style.removeProperty("transform");
            track.style.removeProperty("animation");
        }
        this.$target[0].classList.remove("is-ready");
    },
});

export default options.registry.PartnersLoopOptions;