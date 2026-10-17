import {BaseOptionComponent} from "@html_builder/core/utils";
import {BuilderAction} from "@html_builder/core/builder_action";
import {Plugin} from "@html_editor/plugin";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

/**
 * Website Builder option of the search box: turns the typed examples on or off
 * and edits the prefix and the examples. It writes the hidden list that the
 * public interaction reads (see searchbar_typing.esm.js):
 *
 *     <ul class="o_searchbar_typing d-none" aria-hidden="true">
 *         <li class="o_searchbar_typing_prefix">e.g.</li>
 *         <li>first example</li>
 *     </ul>
 *
 * The option applies to the input, as the standard search options do, so that
 * both are shown in the same panel.
 */
export class SearchbarTypingOption extends BaseOptionComponent {
    static template = "deltatech_website_searchbar_typing.SearchbarTypingOption";
    static selector = ".s_searchbar_input";
    static applyTo = ".search-query";
}

export class BaseSearchbarTypingAction extends BuilderAction {
    static id = "baseSearchbarTyping";

    getFormEl(editingElement) {
        return editingElement.closest(".o_searchbar_form");
    }
    getBoxEl(editingElement) {
        return this.getFormEl(editingElement).querySelector(".o_searchbar_typing");
    }
    getPrefixEl(boxEl) {
        return boxEl?.querySelector(":scope > .o_searchbar_typing_prefix");
    }
    getExampleEls(boxEl) {
        return boxEl ? [...boxEl.querySelectorAll(":scope > li:not(.o_searchbar_typing_prefix)")] : [];
    }
}

export class ToggleSearchbarTypingAction extends BaseSearchbarTypingAction {
    static id = "toggleSearchbarTyping";
    isApplied({editingElement}) {
        return Boolean(this.getBoxEl(editingElement));
    }
    apply({editingElement}) {
        const boxEl = document.createElement("ul");
        boxEl.className = "o_searchbar_typing d-none";
        boxEl.setAttribute("aria-hidden", "true");
        for (const [text, className] of [
            [_t("e.g."), "o_searchbar_typing_prefix"],
            [_t("Example"), ""],
        ]) {
            const itemEl = document.createElement("li");
            if (className) {
                itemEl.className = className;
            }
            itemEl.textContent = text;
            boxEl.append(itemEl);
        }
        this.getFormEl(editingElement).append(boxEl);
    }
    clean({editingElement}) {
        this.getBoxEl(editingElement)?.remove();
    }
}

export class SetSearchbarTypingPrefixAction extends BaseSearchbarTypingAction {
    static id = "setSearchbarTypingPrefix";
    getValue({editingElement}) {
        return this.getPrefixEl(this.getBoxEl(editingElement))?.textContent.trim() || "";
    }
    apply({editingElement, value}) {
        const boxEl = this.getBoxEl(editingElement);
        let prefixEl = this.getPrefixEl(boxEl);
        const prefix = value.trim();
        if (!prefix) {
            prefixEl?.remove();
            return;
        }
        if (!prefixEl) {
            prefixEl = document.createElement("li");
            prefixEl.className = "o_searchbar_typing_prefix";
            boxEl.prepend(prefixEl);
        }
        prefixEl.textContent = prefix;
    }
}

export class SetSearchbarTypingExamplesAction extends BaseSearchbarTypingAction {
    static id = "setSearchbarTypingExamples";
    getValue({editingElement}) {
        const exampleEls = this.getExampleEls(this.getBoxEl(editingElement));
        return JSON.stringify(exampleEls.map((el) => ({value: el.textContent.trim()})));
    }
    apply({editingElement, value}) {
        const boxEl = this.getBoxEl(editingElement);
        for (const exampleEl of this.getExampleEls(boxEl)) {
            exampleEl.remove();
        }
        // An empty item would be an empty translation term: it is not written.
        for (const item of JSON.parse(value)) {
            const text = (item.value || "").trim();
            if (text) {
                const itemEl = document.createElement("li");
                itemEl.textContent = text;
                boxEl.append(itemEl);
            }
        }
    }
}

class SearchbarTypingOptionPlugin extends Plugin {
    static id = "searchbarTypingOption";
    resources = {
        builder_options: [SearchbarTypingOption],
        builder_actions: {
            ToggleSearchbarTypingAction,
            SetSearchbarTypingPrefixAction,
            SetSearchbarTypingExamplesAction,
        },
    };
}

registry.category("website-plugins").add(SearchbarTypingOptionPlugin.id, SearchbarTypingOptionPlugin);
