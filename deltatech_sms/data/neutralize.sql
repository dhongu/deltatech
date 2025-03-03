UPDATE iap_account
    SET sms_secret = false
    where service_name = 'sms';
