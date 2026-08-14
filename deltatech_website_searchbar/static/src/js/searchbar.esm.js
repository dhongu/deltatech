import {patch} from "@web/core/utils/patch";
import {SearchBar} from "@website/snippets/s_searchbar/search_bar";

const MIN_SEARCH_TERM_LENGTH = 4;
const DEBOUNCE_DELAY = 800;

patch(SearchBar.prototype, {
    /**
     * @override
     * Mărește întârzierea de debounce față de cea implicită (400 ms), ca să
     * reducă numărul de apeluri către /website/snippet/autocomplete.
     */
    setup() {
        super.setup();
        this.dynamicContent[".search-query"]["t-on-input"] = this.debounced(this.onInput, DEBOUNCE_DELAY);
    },

    /**
     * @override
     * Interoghează autocomplete-ul doar dacă termenul are cel puțin
     * MIN_SEARCH_TERM_LENGTH caractere.
     */
    async onInput() {
        if (!this.limit) {
            return;
        }
        if (this.inputEl.value.trim().length < MIN_SEARCH_TERM_LENGTH) {
            this.render();
        } else {
            const res = await this.keepLast.add(this.waitFor(this.fetch()));
            this.render(res);
        }
    },
});
