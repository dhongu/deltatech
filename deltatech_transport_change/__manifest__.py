{
    "name": "DeltaTech Transport Change",
    "version": "19.0.0.0.9",
    "category": "Technical",
    "summary": "Export configuration changes to CSV and manage transport through Git",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": [
        "base",
        "mail",
    ],
    "external_dependencies": {
        "python": ["git"],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/transport_config_views.xml",
        "views/transport_repo_views.xml",
    ],
    "installable": True,
    "application": False,
}
