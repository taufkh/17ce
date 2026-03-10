# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib
import hmac
import xmlrpc.client as xmlrpclib
import logging
from unicodedata import normalize
import psycopg2
import werkzeug
import odoo
from odoo import http, _
from odoo.http import request
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, consteq, ustr
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.base_setup.controllers.main import BaseSetup
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.tools.float_utils import float_repr
from datetime import datetime, timedelta
import json
from odoo.exceptions import AccessError, UserError, AccessDenied
import requests

class OdesAPI(http.Controller):

    @http.route('/api/login-user', type='http', auth="public", csrf=False, website=True)
    def login_user(self,**post):
        cr, uid, pool, context = request.cr, odoo.SUPERUSER_ID, request.registry, request.context
        env = request.env(user=odoo.SUPERUSER_ID)
        data_api = request.params
        request.uid = odoo.SUPERUSER_ID
        base_url = env['ir.config_parameter'].sudo().get_param('web.base.url')
        user_obj = env['res.users']
        values = {}
        error = {'code':500}
        if data_api:
            email = data_api.get('email') or False
            password = data_api.get('password') or False
            redirect_type = data_api.get('redirect_type') or False
            if not error.get('message'):
                uid = request.session.authenticate(request.session.db, email, password)
                user = user_obj.sudo().browse(uid)
                base_url = base_url.replace("http://","https://")
                if redirect_type == 'notification':
                    # Production
                    base_url = base_url + '/web#action=112&active_id=mail.box_inbox&cids=1&menu_id=91'

                    # Demo
                    # base_url = base_url + '/web#action=112&active_id=mailbox_inbox&cids=&menu_id=88'
                else:
                    base_url = base_url + '/web'
                redirect = werkzeug.utils.redirect(base_url)
                return redirect

    @http.route('/api/auth-login', type='http', auth="public", csrf=False, website=True)
    def auth_login(self,**post):
        cr, uid, pool, context = request.cr, odoo.SUPERUSER_ID, request.registry, request.context
        env = request.env(user=odoo.SUPERUSER_ID)
        data_api = request.params
        request.uid = odoo.SUPERUSER_ID
        base_url = env['ir.config_parameter'].sudo().get_param('web.base.url')
        db_name = env.cr.dbname
        database_obj = env['odes.apps.database']
        user_obj = env['res.users']
        values = {}
        database_id  = False
        valid = True
        error = {'code':500}

        # Demo
        # urlcompany1 = 'https://ihotel.sgeede.com'
        # urlcompany2 = 'https://login-odes.sgeede.com'
        # urlcompany3 = 'https://dev.odes.com.sg'

        # Production
        urlcompany1 = 'https://odes.com.sg'
        urlcompany2 = 'https://dev2.odes.com.sg'

        if data_api:
            email = data_api.get('email') or False
            password = data_api.get('password') or False
            company_url_name = data_api.get('company_url_name') or False
            registration_id = data_api.get('registration_id') or False
            redirect_type = data_api.get('redirect_type') or False
            database_name = data_api.get('database_name')
            if not company_url_name:
                error['message'] = "Company URL name must be filled"

            # Demo
            # if company_url_name != 'https://ihotel.sgeede.com' and company_url_name != 'https://login-odes.sgeede.com' and company_url_name != 'https://dev.odes.com.sg':
            if company_url_name != urlcompany1 and company_url_name != urlcompany2:
                error['message'] = "Invalid company URL"
            if not password:
                error['message'] = "Password must be filled"
            if not email:
                error['message'] = "Email must be filled"
            if not registration_id:
                error['message'] = "Registration ID must be filled"

            # if company_url_name == 'https://dev.odes.com.sg':
            #     if database_name == 'ODES_TEST' and  email == 'odes-test@gmail.com' and password=='test12345':
            #         values= {
            #         'code': 200,
            #         'message':"You are successfully logged in",
            #         'name':'Odes Test',
            #         'url': 'https://dev.odes.com.sg',
            #         }
            #     else:
            #         error['message'] = 'Invalid Email or Password. Email and password are all case sensitive.'

            #     if error.get('message'):
            #         values = error

            #     json_values = json.dumps(values)
            #     json_return = {'json_values': json_values}
            #     return http.request.render("odes_api.api_odes_apps", json_return)
            # else:
            #     if valid and database_name:
            #         error['message'] = 'The company URL you are using is not listed as multiple databases'

            base_url = company_url_name
            base_url = base_url.replace("http://","https://")
            if not error.get('message'):
                if redirect_type == 'notification':
                    base_url = base_url + '/api/login-user?' + 'email=' + str(email) + '&password=' + str(password) + '&redirect_type=' + str(redirect_type)
                else:
                    base_url = base_url + '/api/login-user?' + 'email=' + str(email) + '&password=' + str(password)
                user = user_obj.sudo().search([('login','=',email)],limit=1)
                
                if not user:
                    error['message'] = 'Invalid Email or Password. Email and password are all case sensitive.'
                try:
                    user._login(db=request.session.db,login=email,password=password,user_agent_env={'interactive':True})
                except odoo.exceptions.AccessDenied as e:
                    error['message'] = 'Invalid Email or Password. Email and password are all case sensitive.'
                try:
                    
                    if registration_id:
                        user.write({'registration_id':registration_id})
                    values= {
                    'code': 200,
                    'message':"You are successfully logged in",
                    'name':user.name,
                    'url': base_url,
                    
                    }
                except odoo.exceptions.AccessDenied as e:
                    error['message'] = 'Invalid Email or Password. Email and password are all case sensitive.'

            if error.get('message'):
                values = error
        
        json_values = json.dumps(values)
        json_return = {'json_values': json_values}
        return http.request.render("odes_api.api_odes_apps", json_return)



    @http.route('/api/auth-db', type='http', auth="public", csrf=False, website=True)
    def auth_db(self,**post):
        cr, uid, pool, context = request.cr, odoo.SUPERUSER_ID, request.registry, request.context
        env = request.env(user=odoo.SUPERUSER_ID)
        data_api = request.params
        request.uid = odoo.SUPERUSER_ID
        base_url = env['ir.config_parameter'].sudo().get_param('web.base.url')
        db_name = env.cr.dbname
        database_obj = env['odes.apps.database']
        user_obj = env['res.users']
        values = {}
        database_id = False
        error = {'code':500}

        # Demo
        # urlcompany1 = 'https://ihotel.sgeede.com'
        # urlcompany2 = 'https://login-odes.sgeede.com'
        # urlcompany3 = 'https://dev.odes.com.sg'

        # Production
        urlcompany1 = 'https://odes.com.sg'
        urlcompany2 = 'https://dev2.odes.com.sg'


        if data_api:
            company_url_name = data_api.get('company_url_name') or False
            if not company_url_name:
                error['message'] = "Company URL name must be filled"

            # if company_url_name != urlcompany1 and company_url_name != urlcompany2 and company_url_name != urlcompany3:
            if company_url_name != urlcompany1 and company_url_name != urlcompany2:
                error['message'] = "Invalid company URL"
            else:
                values= {
                    'code': 200,
                    'message':"Success, Valid Company URL",
                    'url': company_url_name}

            if error.get('message'):
                values = error
        
        json_values = json.dumps(values)
        json_return = {'json_values': json_values}
        return http.request.render("odes_api.api_odes_apps", json_return)


    @http.route('/api/logout', type='http', auth="public", csrf=False, website=True)
    def odes_logout(self,**post):
        cr, uid, pool, context = request.cr, odoo.SUPERUSER_ID, request.registry, request.context
        env = request.env(user=odoo.SUPERUSER_ID)
        data_api = request.params
        request.uid = odoo.SUPERUSER_ID
        base_url = env['ir.config_parameter'].sudo().get_param('web.base.url')
        user_obj = env['res.users']
        redirect= '/web' 
        request.session.logout(keep_db=True)
        return werkzeug.utils.redirect(redirect, 303)


    @http.route('/api/testnofif', type='http', auth="public", csrf=False, website=True)
    def api_testnotif(self,**post):
        cr, uid, pool, context = request.cr, odoo.SUPERUSER_ID, request.registry, request.context
        env = request.env(user=odoo.SUPERUSER_ID)
        data_api = request.params
        request.uid = odoo.SUPERUSER_ID
        base_url = env['ir.config_parameter'].sudo().get_param('web.base.url')
        db_name = env.cr.dbname
        database_obj = env['odes.apps.database']
        user_obj = env['res.users']
        serverToken = 'AAAAQZwUr4o:APA91bGISxxHZxqY1VxUjWJ_j3Ax8tTlmLt1LvQYnxdhiQBgnZpZi9rL5I7evH_ztqil-O09BXWtT5oRdqjHzb3wbB_vjG6I9Jax9mYLwh9UtFfA6K1triK3cnebGH0T3qEHr9hWcvnc'
        values = {}
        database_id = False
        error = {'code':500}
        user_id = False
        if data_api:
            user_id = data_api.get('user_id') or False
            if user_id:
                user_id = int(user_id)
            user = user_obj.search([('id','=',user_id)],limit=1)
            deviceToken = user.registration_id
            login = user.login
            password = 'mobile0_treatment$'+str(user.id)

            base_url = base_url + '/api/login-user?' + 'email=' + str(login) + '&password=' + str(password) + '&redirect_type=notification'
            base_url = base_url.replace("http://","https://")
            if deviceToken and user_id:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'key=' + str(serverToken),
                  }
                body = {
                        'to':deviceToken,
                        'priority': 'high',
                        'notification': {'title': 'Message from Adminstrator',
                                            'content_available':True,
                                            'body': 'Test Notification',
                                            'click_action': 'FLUTTER_NOTIFICATION_CLICK'
                                            },
                        'data' : {'redirection' : str(base_url)}
                        }
                response = requests.post("https://fcm.googleapis.com/fcm/send",headers = headers, data=json.dumps(body))
                values= {
                    'code': 200,
                    'message':"Send Notification Success"}
            else:
                error['message'] = "Send Notification Failed"

        if error.get('message'):
            values = error
        
        json_values = json.dumps(values)
        json_return = {'json_values': json_values}
        return http.request.render("odes_api.api_odes_apps", json_return)
