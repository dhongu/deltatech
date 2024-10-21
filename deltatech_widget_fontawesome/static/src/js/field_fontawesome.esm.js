/** @odoo-module **/

import {registry} from "@web/core/registry";
import {_t} from "@web/core/l10n/translation";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {Component} from "@odoo/owl";

export class FieldFontAwesome extends Component {
    get icon() {
        // Return this.props.icons[this.props.record.data[this.props.name]];
        return "fa " + this.props.record.data[this.props.name];
    }
    get title() {
        return (
            this.props.record.data[this.props.name].charAt(0).toUpperCase() +
            this.props.record.data[this.props.name].slice(1)
        );
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
