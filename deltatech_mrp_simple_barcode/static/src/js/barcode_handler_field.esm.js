/** @odoo-module **/

// Odoo 20 a eliminat widget-ul `barcode_handler` din modulul `barcodes`;
// echivalentul Owl 3: ascultă BarcodePlugin și scrie codul scanat în câmp,
// ceea ce declanșează onchange-ul `_on_barcode_scanned` din modelul `mrp.simple`.

import {Component, usePlugin, useProps, xml} from "@odoo/owl";
import {BarcodePlugin} from "@barcodes/barcode_plugin";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useBus} from "@web/core/utils/hooks";

export class MrpSimpleBarcodeHandlerField extends Component {
    static template = xml``;
    props = useProps(standardFieldProps);

    setup() {
        const barcode = usePlugin(BarcodePlugin);
        useBus(barcode.bus, "barcode_scanned", (ev) => this.onBarcodeScanned(ev));
    }

    onBarcodeScanned(ev) {
        const {barcode} = ev.detail;
        this.props.record.update({[this.props.name]: barcode});
    }
}

export const mrpSimpleBarcodeHandlerField = {
    component: MrpSimpleBarcodeHandlerField,
    supportedTypes: ["char"],
};

registry.category("fields").add("deltatech_mrp_simple_barcode_handler", mrpSimpleBarcodeHandlerField);
