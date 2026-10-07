# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import ipaddress
import logging
import socket
from urllib.parse import urljoin, urlsplit

import requests
import werkzeug

from odoo import api, fields, models
from odoo.tools import image

_logger = logging.getLogger(__name__)

MAX_REDIRECTS = 5
FETCH_TIMEOUT = 15
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MiB
CHUNK_SIZE = 64 * 1024


def _is_public_url(url):
    """Return True only for http(s) URLs whose host resolves exclusively to
    global (public) IP addresses; loopback, private, link-local, multicast and
    reserved ranges (IPv4 and IPv6) are refused, to prevent SSRF."""
    try:
        split = urlsplit(url or "")
        port = split.port or (443 if split.scheme == "https" else 80)
    except ValueError:
        return False
    if split.scheme not in ("http", "https") or not split.hostname:
        return False
    try:
        ips = {str(ipaddress.ip_address(split.hostname))}  # literal IP address, no DNS lookup
    except ValueError:
        try:
            ips = {info[4][0] for info in socket.getaddrinfo(split.hostname, port, proto=socket.IPPROTO_TCP)}
        except (OSError, UnicodeError):
            return False
    if not ips:
        return False
    for ip in ips:
        addr = ipaddress.ip_address(ip.split("%")[0])
        if getattr(addr, "ipv4_mapped", None):
            addr = addr.ipv4_mapped
        if not addr.is_global or addr.is_multicast:
            return False
    return True


class ProductTemplate(models.Model):
    _inherit = "product.template"

    image_file_name = fields.Char(string="Image File Name")

    def _fetch_public_image(self, url):
        """GET an image from a public URL and return its raw bytes, or None.

        Redirects are followed manually so each hop is validated; the body is
        read in streaming mode and capped at MAX_IMAGE_SIZE.
        """
        for _hop in range(MAX_REDIRECTS + 1):
            if not _is_public_url(url):
                _logger.warning("Refused to load product image from non-public URL %s", url)
                return None
            with requests.get(url, timeout=FETCH_TIMEOUT, stream=True, allow_redirects=False) as resp:
                if resp.is_redirect:
                    url = urljoin(url, resp.headers.get("location") or "")
                    continue
                if resp.status_code != 200:
                    return None
                if not (resp.headers.get("content-type") or "").lower().startswith("image/"):
                    return None
                if int(resp.headers.get("content-length") or 0) > MAX_IMAGE_SIZE:
                    return None
                content = b""
                for chunk in resp.iter_content(CHUNK_SIZE):
                    content += chunk
                    if len(content) > MAX_IMAGE_SIZE:
                        return None
                return content
        _logger.warning("Too many redirects while loading product image from %s", url)
        return None

    def _load_image_from_url(self, url):
        """Return the base64 image found at ``url`` or False.

        Only users allowed to modify products may trigger the download
        (onchange can be called with read access only).
        """
        if not url or not self.env["product.template"].has_access("write"):
            return False
        try:
            content = self._fetch_public_image(url.strip())
            if not content:
                return False
            data = base64.b64encode(content)
            image.base64_to_image(data)
        except Exception:
            data = False
        return data

    @api.onchange("image_file_name")
    def onchange_image_file_name(self):
        if self.image_file_name:
            parsed_url = werkzeug.urls.url_parse(self.image_file_name)
            if parsed_url.scheme:
                data = self._load_image_from_url(self.image_file_name)
                if data:
                    self.image_file_name = self.image_file_name.split("/")[-1]
                    self.image_1920 = data

    def write(self, vals):
        if "image_file_name" in vals:
            image_file_name = vals["image_file_name"]
            parsed_url = werkzeug.urls.url_parse(image_file_name)
            if parsed_url.scheme:
                data = self._load_image_from_url(image_file_name)
                if data:
                    vals["image_file_name"] = image_file_name.split("/")[-1]
                    vals["image_1920"] = data
        return super().write(vals)
