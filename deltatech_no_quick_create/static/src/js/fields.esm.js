import {Many2One} from "@web/views/fields/many2one/many2one";
import {patch} from "@web/core/utils/patch";

// Many2OneField, Many2OneBarcodeField, Many2OneAvatarField, ReferenceField, ...
// all render through this shared Many2One component, so patching it here
// disables quick-create everywhere regardless of which widget was used
// (a per-widget patch, e.g. on Many2OneField, misses many2one_barcode and co.).
patch(Many2One.prototype, {
    get many2XAutocompleteProps() {
        return {
            ...super.many2XAutocompleteProps,
            quickCreate: null,
        };
        // Diabled create edit too
        // activeActions: {...super.activeActions, createEdit: false},
    },
});
