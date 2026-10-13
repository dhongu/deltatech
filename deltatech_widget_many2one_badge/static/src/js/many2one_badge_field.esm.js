/** @odoo-module **/

import {ColorList} from "@web/core/colorlist/colorlist";
import {Component, onWillStart, onWillUpdateProps, useState} from "@odoo/owl";
import {
    buildM2OFieldDescription,
    extractM2OFieldProps,
    m2oSupportedOptions,
} from "@web/views/fields/many2one/many2one_field";
import {makeContext} from "@web/core/context";
import {getFieldDomain} from "@web/model/relational_model/utils";
import {Many2XAutocomplete} from "@web/views/fields/relational_utils";
import {registry} from "@web/core/registry";
import {usePopover} from "@web/core/popover/popover_hook";
import {useService} from "@web/core/utils/hooks";

class Many2oneBadgeColorPopover extends Component {
    static template = "deltatech_widget_many2one_badge.ColorPopover";
    static components = {ColorList};
    static props = {
        colors: {type: Array},
        onColorSelected: {type: Function},
        close: {type: Function},
    };
}

export class Many2oneBadgeField extends Component {
    static template = "deltatech_widget_many2one_badge.Many2oneBadgeField";
    static components = {Many2XAutocomplete, Many2oneBadgeColorPopover};
    static RECORD_COLORS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
    static props = {
        "*": true,
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({colorIndex: 0});
        this.popover = usePopover(Many2oneBadgeColorPopover);

        onWillStart(async () => {
            await this._loadColor(this.props);
        });

        onWillUpdateProps(async (nextProps) => {
            await this._loadColor(nextProps);
        });
    }

    async _loadColor(props) {
        const colorField = props.colorField;
        if (!colorField) {
            this.state.colorIndex = 0;
            return;
        }
        const val = props.record.data[props.name];
        if (!val) {
            this.state.colorIndex = 0;
            return;
        }
        const resId = Array.isArray(val) ? val[0] : val.id || val.resId;
        if (!resId) {
            this.state.colorIndex = 0;
            return;
        }
        const relation = props.record.fields[props.name].relation;
        try {
            const result = await this.orm.read(relation, [resId], [colorField]);
            this.state.colorIndex = (result && result[0] && result[0][colorField]) || 0;
        } catch {
            this.state.colorIndex = 0;
        }
    }

    get relation() {
        return this.props.record.fields[this.props.name].relation;
    }

    getDomain() {
        return getFieldDomain(this.props.record, this.props.name, this.props.domain);
    }

    get autocompleteContext() {
        const {context, record} = this.props;
        if (!context) return {};
        if (typeof context === "object") return context;
        try {
            return makeContext([context], record.evalContext);
        } catch {
            return {};
        }
    }

    get activeActions() {
        return {create: false, createEdit: false, write: true};
    }

    async onBadgeClick(ev) {
        if (this.props.readonly || !this.props.colorField) return;
        const val = this.value;
        if (!val) return;
        const resId = Array.isArray(val) ? val[0] : val.id || val.resId;
        if (!resId) return;

        this.popover.open(ev.currentTarget, {
            colors: this.constructor.RECORD_COLORS,
            onColorSelected: async (colorIndex) => {
                await this.orm.write(this.relation, [resId], {
                    [this.props.colorField]: colorIndex,
                });
                this.state.colorIndex = colorIndex;
                this.popover.close();
            },
        });
    }

    async update(records) {
        if (records && records.length) {
            const rec = records[0];
            let displayName = false;
            if ("display_name" in rec) {
                displayName = rec.display_name;
            } else if ("name" in rec) {
                displayName = rec.name && rec.name.id ? rec.name.display_name : rec.name;
            }
            await this.props.record.update({
                [this.props.name]: {id: rec.id, display_name: displayName},
            });
        } else {
            await this.props.record.update({[this.props.name]: false});
        }
        await this._loadColor(this.props);
    }

    async removeValue() {
        await this.props.record.update({[this.props.name]: false});
        this.state.colorIndex = 0;
    }

    get value() {
        return this.props.record.data[this.props.name];
    }

    get displayName() {
        const val = this.value;
        if (!val) return "";
        if (Array.isArray(val)) return val[1];
        return val.display_name || val.displayName || (val.data && val.data.display_name) || "";
    }

    get colorIndex() {
        return this.state.colorIndex;
    }
}

export const many2oneBadgeField = {
    ...buildM2OFieldDescription(Many2oneBadgeField),
    displayName: "Many2one Badge",
    supportedOptions: [
        ...m2oSupportedOptions,
        {
            label: "Color field",
            name: "color_field",
            type: "field",
            availableTypes: ["integer"],
        },
    ],
    extractProps(staticInfo, dynamicInfo) {
        const props = extractM2OFieldProps(staticInfo, dynamicInfo);
        props.colorField = (staticInfo.options && staticInfo.options.color_field) || null;
        props.domain = dynamicInfo.domain;
        return props;
    },
};

registry.category("fields").add("many2one_badge", many2oneBadgeField);
