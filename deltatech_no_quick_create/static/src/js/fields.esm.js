import {Many2OneField} from "@web/views/fields/many2one/many2one_field";
import {patch} from "@web/core/utils/patch";

patch(Many2OneField.prototype, {
    defaultProps: {
        ...Many2OneField.defaultProps,
        canQuickCreate: false,
        quick_create: false,
        no_quick_create: true,
    },
    setup() {
        this.props.canQuickCreate = false;
        // Diabled create edit too
        // this.props.canCreateEdit = false;
        super.setup();
    },
    extractProps({attrs}) {
        const props = super.extractProps(...arguments);
        if (attrs.options.no_quick_create === undefined) props.canQuickCreate = false;
        // Diabled create edit too
        // if (attrs.options.no_create_edit === undefined) props.canCreateEdit = false;
        return props;
    },
});
