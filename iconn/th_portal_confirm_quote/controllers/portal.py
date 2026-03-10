from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.sale.controllers.portal import CustomerPortal


class CustomerPortalConfirmQuote(CustomerPortal):

    @http.route(['/my/orders/<int:order_id>/confirm'], type='http', auth='public', website=True, methods=['POST'])
    def portal_confirm_quote(self, order_id, access_token=None, **kw):
        access_token = access_token or request.params.get('access_token')
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if order_sudo.state not in ('draft', 'sent'):
            return request.redirect(order_sudo.get_portal_url())
        if order_sudo.is_expired:
            return request.redirect(order_sudo.get_portal_url())

        order_sudo.action_confirm()

        return request.redirect(order_sudo.get_portal_url())
