/** @odoo-module */

import {BusinessProjectSharingFormController} from "./business_project_sharing_form_controller.esm";
import {BusinessProjectSharingFormRenderer} from "./business_project_sharing_form_renderer.esm";
import {formView} from "@web/views/form/form_view";

formView.Controller = BusinessProjectSharingFormController;
formView.Renderer = BusinessProjectSharingFormRenderer;
