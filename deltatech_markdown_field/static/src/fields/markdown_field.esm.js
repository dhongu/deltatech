/** @odoo-module **/

import {Component, useRef, onMounted, onPatched} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {_t} from "@web/core/l10n/translation";

/**
 * Field widget "markdown".
 *
 * Stochează Markdown brut într-un câmp Text, dar oferă editare WYSIWYG:
 *  - la încărcare: Markdown -> HTML (marked) și se pune în contenteditable;
 *  - la salvare (blur): HTML -> Markdown (turndown) și se scrie în înregistrare.
 *
 * Librăriile marked / turndown sunt vendorizate ca build-uri UMD și expuse pe
 * globalThis (window.marked / window.TurndownService), la fel ca alte module
 * Terrabit care folosesc librării terțe (vezi deltatech_chatter + split.js).
 */
export class MarkdownField extends Component {
    static template = "deltatech_markdown_field.MarkdownField";
    static props = {
        ...standardFieldProps,
        minHeight: {type: Number, optional: true},
        placeholder: {type: String, optional: true},
    };
    static defaultProps = {
        minHeight: 160,
    };

    setup() {
        this.editorRef = useRef("editor");
        // Markdown-ul reflectat în acest moment în editor; folosit ca să nu
        // suprascriem ce tastează utilizatorul și să detectăm schimbările externe.
        this._lastMarkdown = null;
        this._turndownService = this._buildTurndown();

        onMounted(() => this._renderFromValue());
        onPatched(() => {
            // Schimbare venită din afară (discard, onchange, schimbare de record):
            // reîncărcăm editorul, dar niciodată cât timp utilizatorul scrie în el.
            if (this.markdownValue !== this._lastMarkdown && !this._hasFocus()) {
                this._renderFromValue();
            }
        });
    }

    get markdownValue() {
        return this.props.record.data[this.props.name] || "";
    }

    get readonly() {
        return this.props.readonly;
    }

    // ------------------------------------------------------------------
    // Conversii Markdown <-> HTML
    // ------------------------------------------------------------------
    _buildTurndown() {
        const Turndown = window.TurndownService;
        if (!Turndown) {
            return null;
        }
        return new Turndown({
            headingStyle: "atx",
            codeBlockStyle: "fenced",
            bulletListMarker: "-",
            emDelimiter: "*",
            hr: "---",
        });
    }

    _mdToHtml(md) {
        if (md && window.marked) {
            return window.marked.parse(md, {breaks: true, gfm: true});
        }
        if (!md) {
            return "";
        }
        const div = document.createElement("div");
        div.textContent = md;
        return `<p>${div.innerHTML}</p>`;
    }

    _htmlToMd(html) {
        if (this._turndownService) {
            return this._turndownService.turndown(html).trim();
        }
        // Fallback degradat: text simplu.
        const div = document.createElement("div");
        div.innerHTML = html;
        return (div.textContent || "").trim();
    }

    // ------------------------------------------------------------------
    // Sincronizare editor <-> înregistrare
    // ------------------------------------------------------------------
    _hasFocus() {
        const el = this.editorRef.el;
        return Boolean(el) && document.activeElement === el;
    }

    _renderFromValue() {
        const el = this.editorRef.el;
        if (!el) {
            return;
        }
        el.innerHTML = this._mdToHtml(this.markdownValue);
        this._lastMarkdown = this.markdownValue;
    }

    _commit() {
        const el = this.editorRef.el;
        if (!el || this.readonly) {
            return;
        }
        const md = this._htmlToMd(el.innerHTML);
        if (md !== this._lastMarkdown) {
            this._lastMarkdown = md;
            this.props.record.update({[this.props.name]: md});
        }
    }

    onBlur() {
        this._commit();
    }

    // ------------------------------------------------------------------
    // Bara de unelte (contenteditable + execCommand)
    //
    // execCommand este deprecat dar rămâne universal funcțional pentru
    // editarea unui contenteditable; e compromisul pragmatic pentru un
    // WYSIWYG ușor, fără a cupla widget-ul de editorul html nativ Odoo.
    // ------------------------------------------------------------------
    _exec(command, value = null) {
        if (this.readonly) {
            return;
        }
        this.editorRef.el.focus();
        document.execCommand(command, false, value);
    }

    onToolbar(command, value = null) {
        // Mousedown.prevent păstrează selecția din editor (butonul nu fură focusul).
        if (command === "createLink") {
            const url = window.prompt(_t("Adresă link (URL):"), "https://");
            if (url) {
                this._exec("createLink", url);
            }
            return;
        }
        this._exec(command, value);
    }

    onFormatBlock(tag) {
        // Toggle: dacă suntem deja în blocul respectiv, revenim la paragraf.
        this._exec("formatBlock", `<${tag}>`);
    }
}

export const markdownField = {
    component: MarkdownField,
    displayName: _t("Markdown"),
    supportedTypes: ["text"],
    supportedOptions: [
        {
            label: _t("Minimum height"),
            name: "min_height",
            type: "number",
        },
    ],
    extractProps: ({options, attrs}) => ({
        minHeight: options.min_height ? Number(options.min_height) : undefined,
        placeholder: attrs.placeholder || undefined,
    }),
};

registry.category("fields").add("markdown", markdownField);
