{
    "images": ["static/description/main_screenshot.png"],
    "name": "Transport Change",
    "version": "19.0.0.1.9",
    "license": "LGPL-3",
    "category": "Technical",
    "summary": "Export configuration data to CSV in a Git module, to carry it between databases",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": [
        "base",
        "mail",
    ],
    "external_dependencies": {
        "python": ["GitPython"],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/transport_config_views.xml",
        "views/transport_repo_views.xml",
    ],
    "installable": True,
    "application": False,
}
