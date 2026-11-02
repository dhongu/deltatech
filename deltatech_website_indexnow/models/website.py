# © 2026 Terrabit
# See README.rst file on addons root folder for license details

import logging
import re
import secrets
from urllib.parse import urlsplit

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
# the protocol accepts at most 10,000 URLs in one request
INDEXNOW_BATCH = 10000
KEY_RE = re.compile(r"^[a-zA-Z0-9-]{8,128}$")


class Website(models.Model):
    _inherit = "website"

    indexnow_enabled = fields.Boolean(
        string="IndexNow",
        help="Tell Bing, Yandex, Seznam and Naver every hour which pages were published or changed.",
    )
    indexnow_key = fields.Char(
        string="IndexNow Key",
        copy=False,
        help="8 to 128 letters, digits or dashes. Served at /<key>.txt, so that the search engines "
        "know the site is yours. Generated when IndexNow is enabled; you can paste your own.",
    )
    indexnow_key_url = fields.Char(string="IndexNow Key File", compute="_compute_indexnow_key_url")
    indexnow_last_submit = fields.Datetime(
        string="Last IndexNow Submission",
        copy=False,
        help="Pages changed after this moment are sent at the next run.",
    )
    indexnow_last_run = fields.Datetime(string="Last IndexNow Run", copy=False, readonly=True)
    indexnow_last_result = fields.Char(string="Last IndexNow Result", copy=False, readonly=True)

    @api.depends("indexnow_key", "domain")
    def _compute_indexnow_key_url(self):
        for website in self:
            key = website.indexnow_key
            website.indexnow_key_url = f"{website.get_base_url()}/{key}.txt" if key else False

    @api.constrains("indexnow_key")
    def _check_indexnow_key(self):
        for website in self:
            if website.indexnow_key and not KEY_RE.match(website.indexnow_key):
                raise ValidationError(
                    self.env._("The IndexNow key must have 8 to 128 characters: letters, digits or dashes.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        websites = super().create(vals_list)
        websites._indexnow_prepare()
        return websites

    def write(self, vals):
        res = super().write(vals)
        # an emptied key is generated again, as long as IndexNow stays enabled
        if vals.get("indexnow_enabled") or ("indexnow_key" in vals and not vals["indexnow_key"]):
            self._indexnow_prepare()
        return res

    def _indexnow_prepare(self):
        """A key of its own for each website, and only the changes from now on: the past is sent by hand."""
        for website in self.filtered("indexnow_enabled"):
            vals = {}
            if not website.indexnow_key:
                vals["indexnow_key"] = secrets.token_hex(16)
            if not website.indexnow_last_submit:
                vals["indexnow_last_submit"] = fields.Datetime.now()
            if vals:
                website.write(vals)

    def _indexnow_published_models(self):
        """Models whose published records are public pages of the site, besides website.page.

        A list, not every model with `website.published.mixin`: the mixin also publishes
        records without a page of their own (delivery methods, checkout steps, snippet filters).
        Other modules add their models here.
        """
        names = [
            "website.controller.page",
            "product.template",
            "blog.blog",
            "blog.post",
            "event.event",
            "hr.job",
            "slide.channel",
            "slide.slide",
            "knowledge.article",
        ]
        return [
            name
            for name in names
            if name in self.env and {"website_url", "is_published"} <= set(self.env[name]._fields)
        ]

    def _indexnow_get_urls(self, since=None):
        """Absolute URLs of the public pages of the website, changed after `since` (all without it)."""
        self.ensure_one()
        website = self.with_context(website_id=self.id)
        base_url = self.get_base_url()
        paths = []

        page_domain = [("is_published", "=", True), ("website_indexed", "=", True)]
        if since:
            # the website builder writes the content of a page on its view, not on the page
            page_domain += ["|", ("write_date", ">", since), ("view_id.write_date", ">", since)]
        paths += website._get_website_pages(domain=page_domain).mapped("url")

        for name in self._indexnow_published_models():
            model = self.env[name].sudo().with_context(website_id=self.id)
            domain = [("is_published", "=", True)]
            if "website_indexed" in model._fields:
                domain.append(("website_indexed", "=", True))
            if since:
                domain.append(("write_date", ">", since))
            if "website_id" in model._fields:
                domain += self.website_domain()
            paths += [url for url in model.search(domain).mapped("website_url") if url]

        urls = []
        for path in paths:
            # only the pages of this site: the protocol refuses the URLs of another host
            if path.startswith("/") and not path.startswith("//"):
                url = base_url + path
                if url not in urls:
                    urls.append(url)
        return urls

    def _indexnow_submit(self, urls):
        """Send the URLs to IndexNow; returns (sent, message for the website)."""
        self.ensure_one()
        if not urls:
            return True, self.env._("Nothing to send")
        base_url = self.get_base_url()
        payload = {
            "host": urlsplit(base_url).hostname,
            "key": self.indexnow_key,
            "keyLocation": self.indexnow_key_url,
        }
        for start in range(0, len(urls), INDEXNOW_BATCH):
            batch = urls[start : start + INDEXNOW_BATCH]
            try:
                response = requests.post(
                    INDEXNOW_ENDPOINT,
                    json=dict(payload, urlList=batch),
                    headers={"Content-Type": "application/json; charset=utf-8"},
                    timeout=30,
                )
            except requests.RequestException as error:
                _logger.warning("IndexNow for %s: %s", base_url, error)
                return False, self.env._("Error: %(error)s", error=error)
            if response.status_code not in (200, 202):
                _logger.warning("IndexNow for %s: HTTP %s %s", base_url, response.status_code, response.text)
                return False, self._indexnow_error_message(response.status_code)
        _logger.info("IndexNow for %s: %s URLs sent", base_url, len(urls))
        return True, self.env._("URLs sent: %(count)s", count=len(urls))

    def _indexnow_error_message(self, status):
        messages = {
            400: self.env._("HTTP 400: the request is not valid"),
            403: self.env._("HTTP 403: the key file was not found at %(url)s", url=self.indexnow_key_url),
            422: self.env._(
                "HTTP 422: the URLs do not belong to %(host)s", host=urlsplit(self.get_base_url()).hostname
            ),
            429: self.env._("HTTP 429: too many requests, the next run tries again"),
        }
        return messages.get(status, self.env._("HTTP %(status)s", status=status))

    def _indexnow_run(self, full=False):
        """Send the pages changed since the last submission (all of them with `full`).

        Returns False when a website could not send its pages.
        """
        all_sent = True
        for website in self.filtered(lambda w: w.indexnow_enabled and w.indexnow_key):
            started = fields.Datetime.now()
            since = None if full else website.indexnow_last_submit
            sent, result = website._indexnow_submit(website._indexnow_get_urls(since=since))
            vals = {"indexnow_last_run": started, "indexnow_last_result": result}
            # on an error the same changes are sent again at the next run
            if sent:
                vals["indexnow_last_submit"] = started
            website.write(vals)
            all_sent = all_sent and sent
        return all_sent

    @api.model
    def _cron_indexnow(self):
        self.search([("indexnow_enabled", "=", True)])._indexnow_run()

    def action_indexnow_submit_all(self):
        self.ensure_one()
        if not self.indexnow_enabled or not self.indexnow_key:
            raise UserError(self.env._("Enable IndexNow first."))
        sent = self._indexnow_run(full=True)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("IndexNow"),
                "message": self.indexnow_last_result,
                "type": "success" if sent else "warning",
                "sticky": not sent,
            },
        }
