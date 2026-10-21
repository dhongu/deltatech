import {Component, onWillStart, useState} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {rpc} from "@web/core/network/rpc";

/**
 * Previzualizarea eliminării fundalului pentru o imagine de produs din editor:
 * imaginea înainte și după, metoda aleasă și avertismentul modulului. Nu scrie
 * nimic; „Apply” întoarce metoda aleasă acțiunii din editor.
 */
export class ImageBackgroundDialog extends Component {
    static template = "deltatech_image_optimize.ImageBackgroundDialog";
    static components = {Dialog};
    static props = {
        model: String,
        resId: Number,
        onApply: Function,
        close: Function,
    };

    setup() {
        this.state = useState({
            loading: true,
            method: "auto",
            rembg: true,
            before: false,
            after: false,
            warning: false,
        });
        onWillStart(() => this.preview());
    }

    async preview(method) {
        this.state.loading = true;
        try {
            const result = await rpc("/deltatech_image_optimize/bg/preview", {
                model: this.props.model,
                res_id: this.props.resId,
                method,
            });
            Object.assign(this.state, result);
        } finally {
            this.state.loading = false;
        }
    }

    onMethodChange(ev) {
        this.preview(ev.target.value);
    }

    apply() {
        this.props.onApply(this.state.method);
        this.props.close();
    }
}
