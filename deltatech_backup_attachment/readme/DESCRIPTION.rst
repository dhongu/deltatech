Backup attachments using domain filter

Ex.
 [("mimetype","not in",["image/png", "image/jpeg","application/pdf"])]

 [('res_model','not ilike','product'),('res_model','!=','export.attachment'),('res_field','like','%')]
