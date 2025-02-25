/** @odoo-module */

import {ChatterContainer} from "../../components/chatter/chatter_container.esm";
import {FormRenderer} from "@web/views/form/form_renderer";

export class BusinessProjectSharingFormRenderer extends FormRenderer {}
BusinessProjectSharingFormRenderer.components = {
    ...FormRenderer.components,
    ChatterContainer,
};
