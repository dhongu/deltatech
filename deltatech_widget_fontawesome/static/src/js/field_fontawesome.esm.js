import {Component, t, useProps} from "@odoo/owl";
import {FA_TO_OI} from "./fa_to_oi.esm";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

/**
 * Font Awesome is no longer shipped with Odoo 20.0: icons are Material Symbols
 * rendered with `<i class="oi" data-icon="<name>"/>`.
 * The field value may be a Font Awesome name ("fa-globe", "fa fa-globe", "globe"),
 * translated through the official FA -> Material Symbols mapping, or directly
 * a Material Symbols name ("public", "shopping_cart").
 */
export function parseIconValue(value) {
    if (!value || typeof value !== "string") {
        return {name: "", filled: false};
    }
    const classes = value.trim().split(/\s+/);
    const name = classes.find((cls) => cls !== "fa" && cls !== "oi") || "";
    const faName = name.startsWith("fa-") ? name.slice(3) : name;
    if (faName in FA_TO_OI) {
        const [msName, filled] = FA_TO_OI[faName];
        return {name: msName, filled};
    }
    return {name, filled: false};
}

export class FieldFontAwesome extends Component {
    static template = "fontawesome.FieldFontAwesome";
    props = useProps({
        ...standardFieldProps,
        icons: t.object().optional({}),
    });

    get value() {
        return this.props.record.data[this.props.name];
    }
    get iconData() {
        return parseIconValue(this.value);
    }
    get icon() {
        return this.iconData.name;
    }
    get iconClass() {
        return this.iconData.filled ? "oi oi-filled" : "oi";
    }
    get title() {
        const value = this.value;
        if (!value || typeof value !== "string") {
            return "";
        }
        const label = value
            .trim()
            .replace(/^(fa|oi)\s+/, "")
            .replace(/^fa-/, "")
            .replace(/[-_]/g, " ");
        return label.charAt(0).toUpperCase() + label.slice(1);
    }
}

export const fieldFontAwesome = {
    component: FieldFontAwesome,
    displayName: _t("Icon Selection"),
    supportedTypes: ["char", "text", "selection"],
    extractProps: ({options}) => ({
        icons: options,
    }),
};

registry.category("fields").add("fontawesome", fieldFontAwesome);
