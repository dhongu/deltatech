import {BuilderAction} from "@html_builder/core/builder_action";
import {Plugin} from "@html_editor/plugin";
import {rpc} from "@web/core/network/rpc";
import {registry} from "@web/core/registry";
import {ImageBackgroundDialog} from "./image_background_dialog.esm";

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

// Opțiunea (rândul „Background”) se declară în website.BuilderOptions, vezi image_background_option.xml
export class ImageBackgroundOptionPlugin extends Plugin {
    static id = "dtImageBackgroundOption";
    resources = {
        builder_actions: {RemoveImageBackgroundAction},
    };
}

registry.category("website-plugins").add(ImageBackgroundOptionPlugin.id, ImageBackgroundOptionPlugin);
