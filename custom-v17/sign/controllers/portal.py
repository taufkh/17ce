from odoo import http
from odoo.http import request


class SignPortal(http.Controller):
    @http.route(['/sign/request/<string:token>'], type='http', auth='public', website=True)
    def sign_request_portal(self, token, **kwargs):
        sign_request = request.env['sign.request'].sudo().search([('access_token', '=', token)], limit=1)
        if not sign_request:
            return request.not_found()
        return request.render('sign.sign_request_portal', {'sign_request': sign_request})

    @http.route(['/sign/request/<string:token>/sign/<int:item_id>'], type='http', auth='public', methods=['POST'], website=True, csrf=False)
    def sign_request_item_portal(self, token, item_id, otp='', signature='', **kwargs):
        sign_request = request.env['sign.request'].sudo().search([('access_token', '=', token)], limit=1)
        if not sign_request:
            return request.not_found()
        item = sign_request.request_item_ids.filtered(lambda line: line.id == item_id)[:1]
        if not item:
            return request.not_found()
        item.write({'otp_input': otp, 'signature_text': signature})
        item.with_context(
            signed_ip=request.httprequest.remote_addr,
            signed_user_agent=request.httprequest.user_agent.string,
        ).action_sign_now()
        return request.redirect('/sign/request/%s' % token)
