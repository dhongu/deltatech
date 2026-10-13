import {Component} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {Dialog} from "@web/core/dialog/dialog";
import {ImageField, imageField} from "@web/views/fields/image/image_field";

// Simple dialog showing the product image at full resolution.
export class ImageZoomDialog extends Component {
    static template = "deltatech_sale_catalog_website.ImageZoomDialog";
    static components = {Dialog};
    static props = {
        close: {type: Function, optional: true},
        src: {type: String},
        title: {type: String, optional: true},
    };
}

// Image field that opens the picture full size when clicked (used in the
// Sales product catalog kanban).
export class ImageCatalogZoomField extends ImageField {
    static template = "deltatech_sale_catalog_website.ImageCatalogZoomField";

    setup() {
        super.setup();
        this.dialogService = useService("dialog");
    }

    onImageClick() {
        const {resModel, resId} = this.props.record;
        if (!resId) {
            return;
        }
        this.dialogService.add(ImageZoomDialog, {
            src: `/web/image/${resModel}/${resId}/image_1920`,
            title: this.imgAlt || "",
        });
    }
}

export const imageCatalogZoomField = {
    ...imageField,
    component: ImageCatalogZoomField,
};

registry.category("fields").add("image_catalog_zoom", imageCatalogZoomField);
