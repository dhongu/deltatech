/** @odoo-module */

import {useService} from "@web/core/utils/hooks";
import {createElement} from "@web/core/utils/xml";
import {FormController} from "@web/views/form/form_controller";
import {useViewCompiler} from "@web/views/view_compiler";
import {BusinessProjectSharingChatterCompiler} from "./business_project_sharing_form_compiler.esm";
import {ChatterContainer} from "../../components/chatter/chatter_container.esm";

export class BusinessProjectSharingFormController extends FormController {
    setup() {
        super.setup();
        this.uiService = useService("ui");
        const {arch, xmlDoc} = this.archInfo;
        const template = createElement("t");
        const xmlDocChatter = xmlDoc.querySelector("div.oe_chatter");
        if (xmlDocChatter && xmlDocChatter.parentNode.nodeName === "form") {
            template.appendChild(xmlDocChatter.cloneNode(true));
        }
        const mailTemplates = useViewCompiler(BusinessProjectSharingChatterCompiler, arch, {Mail: template}, {});
        this.mailTemplate = mailTemplates.Mail;
    }

    getActionMenuItems() {
        return {};
    }

    get translateAlert() {
        return null;
    }
}

BusinessProjectSharingFormController.components = {
    ...FormController.components,
    ChatterContainer,
};
