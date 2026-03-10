# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
import json
import logging

import requests
from werkzeug import urls

from odoo import api, fields, models


TIMEOUT = 20

MICROSOFT_AUTH_ENDPOINT = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
MICROSOFT_TOKEN_ENDPOINT = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'

class MicrosoftService(models.AbstractModel):
    _inherit = 'microsoft.service'

    @api.model
    def _get_authorize_uri(self, from_url, service, scope):
        """ This method return the url needed to allow this instance of Odoo to access to the scope
            of gmail specified as parameters
        """
        state = {
            'd': self.env.cr.dbname,
            's': service,
            'f': from_url
        }

        get_param = self.env['ir.config_parameter'].sudo().get_param
        base_url = get_param('web.base.url', default='http://www.odoo.com?NoBaseUrl')
        base_url = base_url.replace('http://','https://')
        client_id = get_param('microsoft_%s_client_id' % (service,), default=False)

        encoded_params = urls.url_encode({
            'response_type': 'code',
            'client_id': client_id,
            'state': json.dumps(state),
            'scope': scope,
            'redirect_uri': base_url + '/microsoft_account/authentication',
            'prompt': 'consent',
            'access_type': 'offline'
        })
        return "%s?%s" % (MICROSOFT_AUTH_ENDPOINT, encoded_params)

    @api.model
    def _get_microsoft_tokens(self, authorize_code, service):
        """ Call Microsoft API to exchange authorization code against token, with POST request, to
            not be redirected.
        """
        get_param = self.env['ir.config_parameter'].sudo().get_param
        base_url = get_param('web.base.url', default='http://www.odoo.com?NoBaseUrl')
        base_url = base_url.replace('http://','https://')
        client_id = get_param('microsoft_%s_client_id' % (service,), default=False)
        client_secret = get_param('microsoft_%s_client_secret' % (service,), default=False)
        scope = self._get_calendar_scope()

        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            'code': authorize_code,
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'authorization_code',
            'scope': scope,
            'redirect_uri': base_url + '/microsoft_account/authentication'
        }
        try:
            dummy, response, dummy = self._do_request(MICROSOFT_TOKEN_ENDPOINT, params=data, headers=headers, method='POST', preuri='')
            access_token = response.get('access_token')
            refresh_token = response.get('refresh_token')
            ttl = response.get('expires_in')
            return access_token, refresh_token, ttl
        except requests.HTTPError:
            error_msg = _("Something went wrong during your token generation. Maybe your Authorization Code is invalid")
            raise self.env['res.config.settings'].get_config_warning(error_msg)