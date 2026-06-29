==============
RPC Audit Log
==============

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/github-dhongu%2Fdeltatech-lightgray.png?logo=github
    :target: https://github.com/dhongu/deltatech/tree/18.0/deltatech_rpc_audit
    :alt: dhongu/deltatech

|badge1| |badge2|

This module logs external **XML-RPC** (``/xmlrpc``, ``/xmlrpc/2``) and
**JSON-RPC** (``/jsonrpc``) calls, so you can audit which integration calls
which model and method, and from where.

For each call to the ``object`` service it logs the client IP, database, user
id, model, method and a trimmed representation of the arguments, under the
logger ``odoo.rpc.audit``. Credentials are never logged.

The real client IP is read from the ``X-Forwarded-For`` header, so calls behind
a reverse proxy (nginx, the Odoo.sh edge) are not all attributed to the proxy
IP (e.g. ``10.0.0.2``), independently of the ``proxy_mode`` server option.

Configuration
=============

Noisy IPs (health checks, monitoring) can be skipped via:

- the config-file key ``rpc_audit_ignore_ips`` (self-hosted), or
- the System Parameter ``rpc_audit.ignore_ips`` (works on Odoo.sh),

both comma separated and merged together.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/dhongu/deltatech/issues>`_.

Credits
=======

Authors
~~~~~~~

* Terrabit

Maintainers
~~~~~~~~~~~

* Dorin Hongu <dhongu>
