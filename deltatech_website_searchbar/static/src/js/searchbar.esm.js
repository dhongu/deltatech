/** @odoo-module **/

import {debounce} from "@web/core/utils/timing";
import searchBar from "@website/snippets/s_searchbar/000";

const MIN_SEARCH_TERM_LENGTH = 4;
const DEBOUNCE_DELAY = 800;

searchBar.searchBar.include({
    /**
     * @override
     * Increase debounce delay and add minimum term length check
     * to reduce the number of requests to /website/snippet/autocomplete
     */
    start() {
        this._onInput = debounce(this._onInput.bind(this), DEBOUNCE_DELAY);
        return this._super(...arguments);
    },

    /**
     * @override
     * Only fetch autocomplete results if term has at least MIN_SEARCH_TERM_LENGTH characters
     */
    _onInput() {
        if (!this.limit) {
            return;
        }
        const term = this.$input.val().trim();
        if (!term.length || term.length < MIN_SEARCH_TERM_LENGTH) {
            this._render();
        } else {
            this.keepLast.add(this._fetch()).then(this._render.bind(this));
        }
    },
});
