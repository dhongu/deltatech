# Part of Terrabit. See LICENSE file for full copyright and licensing details.
"""Reading of public web pages by the server, safely and politely.

- only http(s) addresses whose host resolves to public IP addresses are read (SSRF), and the address
  the connection really reaches is checked again when the socket is opened, so a DNS answer that
  changes between the check and the connection (DNS rebinding) is refused too;
- redirects are followed by hand, at most ``MAX_REDIRECTS``, each one checked the same way;
- the body is read in pieces and cut at a maximum size;
- ``robots.txt`` is respected when asked, and a pause is kept between two requests to the same domain;
- a page of protection against robots (CAPTCHA, Cloudflare challenge, 403/429) only gives the state
  ``blocked``: nothing tries to get around it.
"""

import ipaddress
import logging
import socket
import threading
import time
from dataclasses import dataclass, field
from urllib import robotparser
from urllib.parse import urljoin, urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool

_logger = logging.getLogger(__name__)

MAX_REDIRECTS = 5
TIMEOUT = 15
MAX_PAGE_SIZE = 3 * 1024 * 1024  # 3 MiB
CHUNK_SIZE = 64 * 1024
ROBOTS_TTL = 24 * 3600
ROBOTS_ERROR_TTL = 3600
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; OdooWebScan/1.0)"

ANTIBOT_STATUS = (403, 429, 503)
ANTIBOT_MARKERS = (
    "cf-chl-",
    "challenges.cloudflare.com",
    "/cdn-cgi/challenge-platform/",
    "attention required! | cloudflare",
    "g-recaptcha",
    "www.google.com/recaptcha/",
    "h-captcha",
    "hcaptcha.com/1/api.js",
    "geo.captcha-delivery.com",
    "px-captcha",
)


class UnsafeUrl(Exception):
    """The address is not an http(s) address of a public host"""


@dataclass
class FetchResult:
    """What came out of reading one address

    ``state``: ``ok``, ``not_found`` (404/410), ``blocked`` (robots.txt, protection against robots,
    too many requests), ``refused`` (not a public address) or ``error`` (network, other HTTP status,
    unexpected content type).
    """

    url: str
    state: str
    status: int | None = None
    content: bytes = b""
    content_type: str = ""
    encoding: str | None = None
    detail: str = ""
    headers: dict = field(default_factory=dict)

    @property
    def text(self):
        return self.content.decode(self.encoding or "utf-8", errors="replace")

    @property
    def ok(self):
        return self.state == "ok"


# --------------------------------------------------------------------------- #
#  Public addresses                                                            #
# --------------------------------------------------------------------------- #


def _resolve_host_ips(host, port):
    """:return: every IP address the host name resolves to"""
    return {info[4][0] for info in socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)}


def is_public_ip(ip):
    """:return: True for a global unicast address; loopback, private, link-local, multicast and
    reserved ranges are refused, IPv4 written as IPv6 included"""
    try:
        addr = ipaddress.ip_address(str(ip).split("%")[0])
    except ValueError:
        return False
    if getattr(addr, "ipv4_mapped", None):
        addr = addr.ipv4_mapped
    return addr.is_global and not addr.is_multicast


def check_public_url(url):
    """Raise ``UnsafeUrl`` unless the address is http(s) and its host resolves only to public addresses

    :return: the address
    """
    try:
        split = urlsplit(url or "")
        port = split.port or (443 if split.scheme == "https" else 80)
    except ValueError as e:
        raise UnsafeUrl(f"invalid address: {url}") from e
    if split.scheme not in ("http", "https") or not split.hostname:
        raise UnsafeUrl(f"not an http(s) address: {url}")
    try:
        ips = {str(ipaddress.ip_address(split.hostname))}  # literal IP address, no DNS lookup
    except ValueError:
        try:
            ips = _resolve_host_ips(split.hostname, port)
        except (OSError, UnicodeError) as e:
            raise UnsafeUrl(f"cannot resolve the host {split.hostname}") from e
    if not ips:
        raise UnsafeUrl(f"cannot resolve the host {split.hostname}")
    for ip in ips:
        if not is_public_ip(ip):
            raise UnsafeUrl(f"the host {split.hostname} points to a non-public address ({ip})")
    return url


def is_public_url(url):
    """:return: True when ``check_public_url`` accepts the address"""
    try:
        check_public_url(url)
    except UnsafeUrl:
        return False
    return True


class _PublicPeerMixin:
    """Check the address the socket really reached, against a DNS answer changed after ``check_public_url``"""

    def _new_conn(self):
        sock = super()._new_conn()
        try:
            peer = sock.getpeername()[0]
        except OSError:
            peer = None
        if not is_public_ip(peer):
            sock.close()
            raise UnsafeUrl(f"the connection to {self.host} reached a non-public address ({peer})")
        return sock


class _PublicHTTPConnection(_PublicPeerMixin, HTTPConnection):
    pass


class _PublicHTTPSConnection(_PublicPeerMixin, HTTPSConnection):
    pass


class _PublicHTTPConnectionPool(HTTPConnectionPool):
    ConnectionCls = _PublicHTTPConnection


class _PublicHTTPSConnectionPool(HTTPSConnectionPool):
    ConnectionCls = _PublicHTTPSConnection


class PublicOnlyAdapter(HTTPAdapter):
    """A requests adapter whose connections can only reach public addresses"""

    def init_poolmanager(self, *args, **kwargs):
        result = super().init_poolmanager(*args, **kwargs)
        self.poolmanager.pool_classes_by_scheme = {
            "http": _PublicHTTPConnectionPool,
            "https": _PublicHTTPSConnectionPool,
        }
        return result


def new_session(user_agent=None):
    """:return: a requests session that only reaches public addresses; the proxies of the environment
    are not used, as the address checked would then be the one of the proxy"""
    session = requests.Session()
    session.trust_env = False
    adapter = PublicOnlyAdapter()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers["User-Agent"] = user_agent or DEFAULT_USER_AGENT
    return session


def domain_of(url):
    """:return: the host of the address, in lower case, without ``www.``"""
    host = (urlsplit(url or "").hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def is_excluded(url, excluded_domains):
    """:return: True when the host of the address is one of the excluded domains or one of their subdomains"""
    host = domain_of(url)
    return any(host == d or host.endswith("." + d) for d in excluded_domains or ())


# --------------------------------------------------------------------------- #
#  Politeness                                                                  #
# --------------------------------------------------------------------------- #

_lock = threading.Lock()
_last_request = {}  # domain -> time.monotonic() of the last request
_robots_cache = {}  # scheme://host -> (parser or None, expiry)


def throttle(domain, delay):
    """Wait until ``delay`` seconds have passed since the last request to the domain, in this process"""
    if not delay or not domain:
        return
    with _lock:
        now = time.monotonic()
        wait = _last_request.get(domain, 0) + delay - now
        _last_request[domain] = now + max(wait, 0)
    if wait > 0:
        time.sleep(wait)


def _http_get(session, url, **kwargs):
    """The one place where the network is reached; the tests replace it"""
    return session.get(url, **kwargs)


def _read_robots(base, session, delay):
    """:return: the parser of the robots.txt of the site, or None when every page may be read"""
    url = base + "/robots.txt"
    throttle(domain_of(url), delay)
    result = _get(url, session=session, max_size=512 * 1024, accept=None)
    if result.status and 400 <= result.status < 500:
        return None, ROBOTS_TTL  # no robots.txt: everything is allowed
    if not result.ok:
        return None, ROBOTS_ERROR_TTL
    parser = robotparser.RobotFileParser(url)
    parser.parse(result.text.splitlines())
    return parser, ROBOTS_TTL


def robots_allowed(url, user_agent=None, session=None, delay=0):
    """:return: True when the robots.txt of the site lets ``user_agent`` read the address (cached for a day)"""
    split = urlsplit(url)
    base = f"{split.scheme}://{split.netloc}"
    now = time.monotonic()
    with _lock:
        cached = _robots_cache.get(base)
    if not cached or cached[1] < now:
        parser, ttl = _read_robots(base, session or new_session(user_agent), delay)
        cached = (parser, now + ttl)
        with _lock:
            _robots_cache[base] = cached
    parser = cached[0]
    return parser is None or parser.can_fetch(user_agent or DEFAULT_USER_AGENT, url)


def clear_caches():
    """Forget the robots.txt read and the time of the last requests (for the tests)"""
    with _lock:
        _robots_cache.clear()
        _last_request.clear()


def is_antibot(status, text=""):
    """:return: True when the answer is a refusal or a test against robots, not the page asked for"""
    if status in ANTIBOT_STATUS:
        return True
    head = (text or "")[:200000].lower()
    return any(marker in head for marker in ANTIBOT_MARKERS)


# --------------------------------------------------------------------------- #
#  Reading                                                                     #
# --------------------------------------------------------------------------- #


def _get(url, session, headers=None, max_size=MAX_PAGE_SIZE, accept=("html",)):
    """Read an address, following and checking the redirects, without robots.txt and pause"""
    for _hop in range(MAX_REDIRECTS + 1):
        try:
            check_public_url(url)
        except UnsafeUrl as e:
            return FetchResult(url, "refused", detail=str(e))
        try:
            with _http_get(session, url, headers=headers, timeout=TIMEOUT, stream=True, allow_redirects=False) as resp:
                if resp.is_redirect:
                    url = urljoin(url, resp.headers.get("location") or "")
                    continue
                content_type = (resp.headers.get("content-type") or "").lower()
                content = b""
                for chunk in resp.iter_content(CHUNK_SIZE):
                    content += chunk
                    if len(content) > max_size:
                        content = content[:max_size]
                        break
                result = FetchResult(
                    url,
                    "ok",
                    status=resp.status_code,
                    content=content,
                    content_type=content_type,
                    encoding=resp.encoding,
                    headers=dict(resp.headers),
                )
        except UnsafeUrl as e:
            return FetchResult(url, "refused", detail=str(e))
        except requests.RequestException as e:
            return FetchResult(url, "error", detail=str(e))
        if resp.status_code in (404, 410):
            result.state, result.detail = "not_found", f"HTTP {resp.status_code}"
        elif is_antibot(resp.status_code, result.text if resp.status_code != 200 or "html" in content_type else ""):
            result.state, result.detail = "blocked", f"HTTP {resp.status_code}: protection against robots"
        elif resp.status_code != 200:
            result.state, result.detail = "error", f"HTTP {resp.status_code}"
        elif accept and not any(kind in content_type for kind in accept):
            result.state, result.detail = "error", f"unexpected content type {content_type or '?'}"
        return result
    return FetchResult(url, "error", detail="too many redirects")


def fetch(
    url,
    session=None,
    headers=None,
    user_agent=None,
    respect_robots=True,
    delay=0,
    max_size=MAX_PAGE_SIZE,
    accept=("html",),
):
    """Read a public page, politely

    :param session: a session from ``new_session`` (to keep cookies, after a login); a new one otherwise
    :param respect_robots: do not read an address that robots.txt forbids (state ``blocked``)
    :param delay: seconds to wait between two requests to the same domain
    :param accept: parts of the content type accepted (None: any)
    :return: a ``FetchResult``; network problems never raise
    """
    session = session or new_session(user_agent)
    user_agent = user_agent or session.headers.get("User-Agent")
    try:
        check_public_url(url)
    except UnsafeUrl as e:
        return FetchResult(url, "refused", detail=str(e))
    if respect_robots and not robots_allowed(url, user_agent, session, delay):
        return FetchResult(url, "blocked", detail="forbidden by robots.txt")
    throttle(domain_of(url), delay)
    return _get(url, session, headers=headers, max_size=max_size, accept=accept)
