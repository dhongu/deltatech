import {Component} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

export class FieldFontAwesome extends Component {
    get value() {
        // Unset fields are `false` in Odoo; normalize to a string.
        return this.props.record.data[this.props.name] || "";
    }
    get icon() {
        return this.value ? `fa ${this.value}` : "";
    }
    get title() {
        const value = this.value;
        return value ? value.charAt(0).toUpperCase() + value.slice(1) : "";
    }
}

FieldFontAwesome.template = "fontawesome.FieldFontAwesome";
FieldFontAwesome.props = {
    ...standardFieldProps,
    icons: Object,
};

export const fieldFontAwesome = {
    component: FieldFontAwesome,
    displayName: _t("Icon Selection"),
    supportedTypes: ["char", "text", "selection"],
    extractProps: ({options}) => ({
        icons: options,
    }),
};

registry.category("fields").add("fontawesome", fieldFontAwesome);
