{
    "name": "Deltatech Replenishment Explain",
    "version": "18.0.1.1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Inventory",
    "summary": "Explain how and why a reordering rule reached its forecast and to-order quantity, "
    "and flag visibility/horizon stockout risks.",
    "depends": ["stock"],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "views/replenishment_explanation_templates.xml",
        "wizard/stock_replenishment_explanation_views.xml",
        "views/stock_orderpoint_views.xml",
        "data/replenishment_explain_server_action.xml",
    ],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}

