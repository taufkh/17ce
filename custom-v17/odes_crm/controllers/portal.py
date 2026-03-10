# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class CustomerPortal(CustomerPortal):
    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        if request.env['res.users'].sudo().browse(request.session.uid).has_group('odes_crm.group_odes_customer'):
            return http.local_redirect('/web')
        return super(CustomerPortal, self).home(**kw)