# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license detailsimport odoo

odoo.release.version_info = odoo.release.version_info[:5] + ("e",)
if "+e" not in odoo.release.version:  # not already patched by packaging
    odoo.release.version = "{0}+ec{1}{2}".format(*odoo.release.version.partition("-"))

odoo.service.common.RPC_VERSION_1.update(
    server_version=odoo.release.version, server_version_info=odoo.release.version_info
)
