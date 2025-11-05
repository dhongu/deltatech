{
    "name": "DeltaTech Transport Change",
    "version": "19.0.0.1.8",
    "category": "Technical",
    "summary": "Export configuration changes to CSV and manage transport through Git",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": [
        "base",
        "mail",
        "deltatech_test_system",
    ],
    "external_dependencies": {
        "python": ["GitPython"],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/transport_config_views.xml",
        "views/transport_repo_views.xml",
        "views/ir_model_view.xml",
    ],
    "installable": True,
    "application": False,
}
