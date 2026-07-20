import {SearchModel} from "@web/search/search_model";

/**
 * The standard category search-panel only emits a `child_of` operator for
 * many2one fields (see SearchModel._getCategoryDomain). Website categories are
 * stored in the many2many `public_categ_ids`, so without this override selecting
 * a parent category would use `=` and miss the products of its sub-categories.
 * We relax the condition so the hierarchy cascades on many2many too.
 */
export class ProductCatalogWebsiteSearchModel extends SearchModel {
    _getCategoryDomain(excludedCategoryId) {
        const domain = [];
        for (const category of this.categories) {
            if (category.id === excludedCategoryId || !category.activeValueId) {
                continue;
            }
            const field = this.searchViewFields[category.fieldName];
            const isHierarchical = category.parentField && (field.type === "many2one" || field.type === "many2many");
            const operator = isHierarchical ? "child_of" : "=";
            domain.push([category.fieldName, operator, category.activeValueId]);
        }
        return domain;
    }
}
