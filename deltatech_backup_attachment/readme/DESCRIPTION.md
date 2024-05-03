Backup attachments using domain filter

  - Ex.  
    \[("mimetype","not in",\["image/png",
    "image/jpeg","application/pdf"\])\]
    
    \[('res\_model','not
    ilike','product'),('res\_model','\!=','export.attachment'),('res\_field','like','%')\]
