import {registry} from "@web/core/registry";
import {productCatalogKanbanView} from "@product/product_catalog/kanban_view";
import {ProductCatalogWebsiteSearchModel} from "./search_model.esm";

// Same catalog kanban as the standard one, but with a SearchModel that lets the
// website-category tree (public_categ_ids, a many2many) cascade with `child_of`.
export const productCatalogWebsiteKanbanView = {
    ...productCatalogKanbanView,
    SearchModel: ProductCatalogWebsiteSearchModel,
};

registry.category("views").add("product_kanban_catalog_website", productCatalogWebsiteKanbanView);
