UPDATE iap_account
    SET endpoint = false, sms_secret = false
    where service_name = 'sms';
