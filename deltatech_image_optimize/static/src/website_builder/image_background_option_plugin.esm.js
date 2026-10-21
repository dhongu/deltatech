import {BuilderAction} from "@html_builder/core/builder_action";
import {BaseOptionComponent} from "@html_builder/core/utils";
import {REPLACE_MEDIA} from "@html_builder/utils/option_sequence";
import {Plugin} from "@html_editor/plugin";
import {withSequence} from "@html_editor/utils/resource";
import {rpc} from "@web/core/network/rpc";
import {registry} from "@web/core/registry";
import {ImageBackgroundDialog} from "./image_background_dialog.esm";

// Imaginile de produs din pagină: câmpul imaginii pe produs, variantă sau galerie
export const PRODUCT_IMAGE_SELECTOR = ["product.template", "product.product", "product.image"]
    .map((model) => `[data-oe-type='image'][data-oe-model='${model}'][data-oe-field='image_1920'] > img`)
    .join(", ");

export class ImageBackgroundOption extends BaseOptionComponent {
    static template = "deltatech_image_optimize.ImageBackgroundOption";
    static selector = PRODUCT_IMAGE_SELECTOR;
}

/**
 * Elimină fundalul imaginii de produs. Imaginea ține de produs, nu de pagină:
 * se scrie pe server, apoi editorul salvează și reîncarcă pagina, ca la
 * butoanele standard ale imaginilor de produs (ordine, ștergere).
 */
export class RemoveImageBackgroundAction extends BuilderAction {
    static id = "dtRemoveImageBackground";

    setup() {
        this.reload = {};
        this.canTimeout = false;
    }

    async load({editingElement: el}) {
        const {oeModel, oeId} = el.parentElement.dataset;
        return new Promise((resolve) => {
            this.services.dialog.add(
                ImageBackgroundDialog,
                {
                    model: oeModel,
                    resId: parseInt(oeId, 10),
                    onApply: (method) => resolve({method}),
                },
                {onClose: () => resolve(false)}
            );
        });
    }

    async apply({editingElement: el, loadResult}) {
        if (!loadResult) {
            return BuilderAction.cancelReload;
        }
        const {oeModel, oeId} = el.parentElement.dataset;
        await rpc("/deltatech_image_optimize/bg/apply", {
            model: oeModel,
            res_id: parseInt(oeId, 10),
            method: loadResult.method,
        });
    }
}

export class ImageBackgroundOptionPlugin extends Plugin {
    static id = "dtImageBackgroundOption";
    resources = {
        builder_options: [withSequence(REPLACE_MEDIA, ImageBackgroundOption)],
        builder_actions: {RemoveImageBackgroundAction},
    };
}

registry.category("website-plugins").add(ImageBackgroundOptionPlugin.id, ImageBackgroundOptionPlugin);
