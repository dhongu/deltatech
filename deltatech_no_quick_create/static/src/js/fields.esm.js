/** @odoo-module **/

import {Many2OneField} from "@web/views/fields/many2one/many2one_field";

const extractProps = Many2OneField.extractProps;

Many2OneField.extractProps = ({attrs, field}) => {
    const props = extractProps({attrs, field});
    if (attrs.options.no_quick_create === undefined) props.canQuickCreate = false;
    return props;
};
