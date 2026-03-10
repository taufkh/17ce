# -*- coding: utf-8 -*-
from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.sale.controllers.portal import CustomerPortal

class CustomerPortal(CustomerPortal):

    @http.route(['/my/orders/<int:order_id>'], type='http', auth="public", website=True)
    def portal_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            if order_sudo.quotation_type != 'service':
                # return self._show_report(model=order_sudo, report_type=report_type, report_ref='sale.action_report_saleorder', download=download)
                return self._show_report(model=order_sudo, report_type=report_type, report_ref='odes_custom.report_sale_order', download=download) #kalo ga sempat hardcode
            if order_sudo.quotation_type == 'service':
                return self._show_report(model=order_sudo, report_type=report_type, report_ref='odes_quotation.action_report_service_quotation', download=download)
        else:
            return super(CustomerPortal, self).portal_order_page(order_id, report_type=report_type, access_token=access_token, message=message, download=download, **kw)