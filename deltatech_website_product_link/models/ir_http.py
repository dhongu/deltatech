from odoo import _, api, exceptions, models
from odoo.http import local_redirect, request


class NoOriginError(exceptions.ValidationError):
    pass


class NoRedirectionError(exceptions.ValidationError):
    pass


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _dispatch(cls):
        """Handle SEO-redirected URLs."""
        # Only handle redirections for HTTP requests
        path = request.httprequest.path
        if not (hasattr(request, "jsonrequest") or path.startswith("/web") or path.startswith("/shop")):
            wsr = request.env["ir.http"].sudo()

            # Requests at this point have no user, must remove `env` to force
            # Odoo recompute it next time a controller needs it, with its user
            # del request._env
            try:
                # Make Odoo believe it is in the original controller
                return cls.reroute(wsr.find_origin())
            except NoOriginError:
                pass
            try:
                # Redirect user to SEO version of this URL if possible
                return wsr.redirect_auto()
            except NoRedirectionError:
                try:
                    # Make Odoo believe it is in the original controller
                    return cls.reroute(wsr.find_origin())
                except NoOriginError:
                    pass

        return super(IrHttp, cls)._dispatch()

    @api.model
    def redirect_auto(self, path=None, code=301, website=None, rerouting=None):
        """Return a redirection for the SEO path or fail.

        :param str path:
            Path that will be searched among the SEO redirections.

        :param int code:
            HTTP redirection code.

        :param website odoo.models.Model:
            Current website object. Default: ``request.website``.

        :param list rerouting:
            List of reroutings performed. It defaults to ``request.rerouting``.

        :raise NoRedirectionError:
            If no redirection target is found. This allows you to continue
            the normal behavior in your controller.

        :return werkzeug.wrappers.Response:
            Redirection to the SEO version of the URL.
        """
        # Default values
        path = path or request.httprequest.path
        rerouting = rerouting or getattr(request, "rerouting", list())
        website = website or getattr(request, "website", self.env["website"].get_current_website())

        # match = self.search([("origin", "=", path)])
        Category = request.env["product.public.category"]
        match = Category.search([("website_url", "=", path)], limit=1)
        # if not match:
        #     Product = self.env['product.template']
        #     match = Product.search([("alternative_link", "=", path)], limit=1)
        destination = match.alternative_link
        # Fail when needed
        if not destination:
            raise NoRedirectionError(_("No redirection target found."))
        if destination in rerouting:
            raise NoRedirectionError(_("Duplicated redirection."))

        # Add language prefix to URL
        if website.default_lang_code != request.lang and request.lang in website.language_ids.mapped("code"):
            destination = "/{}{}".format(request.lang, destination)

        # Redirect to the SEO URL
        return local_redirect(destination, dict(request.httprequest.args), True, code=code)

    @api.model
    def find_origin(self, redirected_path=None):
        """Finds the original path for :param:`redirected_path`.

        :param str redirected_path:
            Destination path to get to a controller.

        :raise NoOriginError:
            When no original URL is found, or the found URL is not marked with
            :attr:`relocate_controller`.

        :return str:
            Returns the original path (e.g. ``/page/example``) if
            :attr:`redirected_path` (e.g. ``/example``) is found among the SEO
            redirections, or :attr:`redirected_path` itself otherwise.
        """
        path = redirected_path or request.httprequest.path

        Category = request.env["product.public.category"]
        match = Category.search([("alternative_link", "=", path)], limit=1)
        if not match:
            Product = self.env["product.template"].with_context(origin=True, active_test=False)
            match = Product.search([("alternative_link", "=", path)], limit=1)
        if not match:
            raise NoOriginError(_("No origin found for this redirection."))
        return match.with_context(origin=True).website_url
