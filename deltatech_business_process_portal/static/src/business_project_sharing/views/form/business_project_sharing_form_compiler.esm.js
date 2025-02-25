/** @odoo-module */

import {append, createElement, setAttributes} from "@web/core/utils/xml";
import {FormCompiler} from "@web/views/form/form_compiler";
import {ViewCompiler, getModifier} from "@web/views/view_compiler";
import {patch} from "@web/core/utils/patch";
import {registry} from "@web/core/registry";
import {SIZES} from "@web/core/ui/ui_service";

/**
 * Compiler the portal chatter in project sharing.
 *
 * @param {HTMLElement} node
 * @param {Object} params
 * @returns
 */
function compileChatter(node, params) {
    const chatterContainerXml = createElement("ChatterContainer");
    const parentURLQuery = new URLSearchParams(window.parent.location.search);
    setAttributes(chatterContainerXml, {
        token: `'${parentURLQuery.get("access_token")}'` || "",
        resModel: params.resModel,
        resId: params.resId,
        BusinessProjectSharingId: params.BusinessProjectSharingId,
    });
    const chatterContainerHookXml = createElement("div");
    chatterContainerHookXml.classList.add("o_FormRenderer_chatterContainer");
    append(chatterContainerHookXml, chatterContainerXml);
    return chatterContainerHookXml;
}

export class BusinessProjectSharingChatterCompiler extends ViewCompiler {
    setup() {
        this.compilers.push({selector: "t", fn: this.compileT});
        this.compilers.push({selector: "div.oe_chatter", fn: this.compileChatter});
    }

    compile(node, params) {
        const res = super.compile(node, params).children[0];
        const chatterContainerHookXml = res.querySelector(".o_FormRenderer_chatterContainer");
        if (chatterContainerHookXml) {
            setAttributes(chatterContainerHookXml, {
                "t-if": `uiService.size >= ${SIZES.XXL}`,
            });
            chatterContainerHookXml.classList.add("overflow-x-hidden", "overflow-y-auto", "o-aside", "h-100");
        }
        return res;
    }

    compileT(node, params) {
        const compiledRoot = createElement("t");
        for (const child of node.childNodes) {
            const invisible = getModifier(child, "invisible");
            let compiledChild = this.compileNode(child, params, false);
            compiledChild = this.applyInvisible(invisible, compiledChild, {
                ...params,
                recordExpr: "model.root",
            });
            append(compiledRoot, compiledChild);
        }
        return compiledRoot;
    }

    compileChatter(node) {
        return compileChatter(node, {
            resId: "model.root.resId or undefined",
            resModel: "model.root.resModel",
            BusinessProjectSharingId: "model.root.context.active_id",
        });
    }
}

registry.category("form_compilers").add("portal_chatter_compiler", {
    selector: "div.oe_chatter",
    fn: (node) =>
        compileChatter(node, {
            resId: "props.record.resId or undefined",
            resModel: "props.record.resModel",
            BusinessProjectSharingId: "props.record.context.active_id",
        }),
});

patch(FormCompiler.prototype, "business_project_sharing_chatter", {
    compile(node, params) {
        const res = this._super(node, params);
        const chatterContainerHookXml = res.querySelector(".o_FormRenderer_chatterContainer");
        if (!chatterContainerHookXml) {
            return res; // No chatter, keep the result as it is
        }
        if (chatterContainerHookXml.parentNode.classList.contains("o_form_sheet")) {
            return res; // If chatter is inside sheet, keep it there
        }
        const formSheetBgXml = res.querySelector(".o_form_sheet_bg");
        const parentXml = formSheetBgXml && formSheetBgXml.parentNode;
        if (!parentXml) {
            return res; // Miss-config: a sheet-bg is required for the rest
        }
        // After sheet bg (standard position, below form)
        setAttributes(chatterContainerHookXml, {
            "t-if": `uiService.size < ${SIZES.XXL}`,
        });
        append(parentXml, chatterContainerHookXml);
        return res;
    },
});
