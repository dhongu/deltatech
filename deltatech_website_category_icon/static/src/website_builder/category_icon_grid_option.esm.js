import {BaseOptionComponent} from "@html_builder/core/utils";
import {Plugin} from "@html_editor/plugin";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class CategoryIconGridOption extends BaseOptionComponent {
    static template = "deltatech_website_category_icon.CategoryIconGridOption";
    static selector = ".s_category_icon_grid";

    setup() {
        super.setup();
        this.website = useService("website");
    }

    get categoryDomain() {
        return [["website_id", "in", [false, this.website.currentWebsiteId]]];
    }
}

class CategoryIconGridOptionPlugin extends Plugin {
    static id = "categoryIconGridOption";
    resources = {
        builder_options: [CategoryIconGridOption],
    };
}

registry.category("website-plugins").add(CategoryIconGridOptionPlugin.id, CategoryIconGridOptionPlugin);
