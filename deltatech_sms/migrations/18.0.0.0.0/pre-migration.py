import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("_____________ Migration pre-script for IAP ANAF _____________")

    # cr.execute("""
    #     UPDATE iap_service SET technical_name = 'sms_old' WHERE technical_name = 'sms';
    # """)
