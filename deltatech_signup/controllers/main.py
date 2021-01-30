import logging
import werkzeug

import openerp
from openerp.addons.auth_signup.res_users import SignupError
from openerp.addons.web.controllers.main import ensure_db
from openerp.addons.auth_signup.controllers.main import AuthSignupHome
from openerp import http
from openerp.http import request
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)

class ExtensionAuthSignupHome(AuthSignupHome):
    
    @http.route()
    def web_login(self, *args, **kw):
        #do_before()
        return super(ExtensionAuthSignupHome, self).web_login(*args, **kw)
    
   
    def do_signup(self, qcontext):

        #return super(ExtensionAuthSignupHome, self).do_signup( qcontext)
        
        values = dict((key, qcontext.get(key)) for key in ('login', 'name', 'password','vat'))
        assert any([k for k in values.values()]), "The form was not properly filled in."
        assert values.get('password') == qcontext.get('confirm_password'), "Passwords do not match; please retype them."
        values['lang'] = request.lang
        
        #vat =  qcontext.get('vat', False) 
        
        #assert vat, "The field VAT was not properly filled in."
        company_id = request.registry['res.company'].create(request.cr, openerp.SUPERUSER_ID,{'name':values['vat']})
        company = request.registry['res.company'].browse(request.cr, openerp.SUPERUSER_ID, company_id)
        request.registry['res.partner'].button_get_partner_data(request.cr, openerp.SUPERUSER_ID, company.partner_id.id )
        #values['partner_id'] = company.partner_id.id        
        values['company_id'] = company.id
        values['company_ids'] = [(6, 0, [company.id])]
        self._signup_with_values(qcontext.get('token'), values)
        request.cr.commit()
        


        