import {SearchBar} from "@website/snippets/s_searchbar/search_bar";
import {patch} from "@web/core/utils/patch";

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
     * MIN_SEARCH_TERM_LENGTH caractere; un termen mai scurt e tratat ca unul gol
     * (meniul se închide, contorul de rezultate revine la 0).
     */
    async onInput() {
        if (!this.limit) {
            return;
        }
        const length = this.inputEl.value.trim().length;
        if (length && length < MIN_SEARCH_TERM_LENGTH) {
            // Anulează un răspuns încă în așteptare pentru un termen mai lung
            this.keepLast.add(Promise.resolve());
            this.render(null);
            this.updateButtonContent(0);
            return;
        }
        return super.onInput();
    },
});
