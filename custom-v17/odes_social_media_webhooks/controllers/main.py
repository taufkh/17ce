# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import requests
import werkzeug
import urllib.parse
from werkzeug.urls import url_encode, url_join

from odoo import http, _
from odoo.http import request 

import logging
_logger = logging.getLogger(__name__)
 
from multiprocessing.dummy import Pool
pool = Pool()

class OdesSocialMediaWebhooks(http.Controller): 
    def on_success(self, r):
        print('succeed',r)

    def on_error(self, ex):
        print('failed',ex)

    def call_api(self, url, data): #type Json
        requests.post(url=url, json=data)

    def pool_processing_create(self, url, data, headers=False):
        pool.apply_async(self.call_api, args=[url, data], 
        callback=self.on_success, error_callback=self.on_error)

    """
        IMPORTANT : 
        For verification facebook is send using http, and for send Message data using json. because Odoo can't handle 2 type request you must manually edit http for then change to json.
    """

    """
    @http.route(['/odes_social_media_webhooks/facebook/callback'], type='http', auth='public', csrf=False)
    def webhooks_facebook_callback_http(self, **kw):
        return kw.get('hub.challenge','failed')

    @http.route(['/odes_social_media_webhooks/instagram/callback'], type='http', auth='public', csrf=False)
    def webhooks_instagram_callback_http(self, **kw):
        return kw.get('hub.challenge','failed')
    """

    # ======================================================================================


    @http.route(['/odes_social_media_webhooks/facebook/callback'], type='json', auth='public', csrf=False)
    def webhooks_facebook_callback(self, **post):
        webhooks = request.env['odes.social.media.webhooks'].sudo().search([('media_type','=','facebook')])
        data = post
        try:
            data = request.jsonrequest # To get Facebook Callback Data
        except Exception as e:
            print('Exception: ~ ',e)
        if data: 
            for webhook in webhooks:
                callback_url = webhook.callback_url
                try:
                    self.pool_processing_create(callback_url,data)
                except Exception as e:
                    print('Exception: facebook ~ ',e)
        return post.get('hub.challenge',json.dumps(data))

    @http.route(['/odes_social_media_webhooks/instagram/callback'], type='json', auth='public', csrf=False)
    def webhooks_instagram_callback(self, **post):
        webhooks = request.env['odes.social.media.webhooks'].sudo().search([('media_type','=','instagram')])
        data = post
        try:
            data = request.jsonrequest # To get Instagram Callback Data
        except Exception as e:
            print('Exception: ~ ',e)
        if data: 
            for webhook in webhooks:
                callback_url = webhook.callback_url
                try:
                    self.pool_processing_create(callback_url,data)
                except Exception as e:
                    print('Exception: instagram ~ ',e)
        return post.get('hub.challenge',json.dumps(data))




    @http.route(['/odes_social_media_webhooks/facebook/account_callback_redirect'], type='http', auth='user')
    def facebook_account_callback_redirect(self, **kw):
        """ Help to redirect callback facebook account, to not https domain """ 
        print("kw::",kw)

        webhook = request.env['odes.social.media.webhooks'].sudo().search([('media_type','=','facebook_account_callback_redirect')], limit=1)
        if webhook:
            url = '%s?%s' % (webhook.callback_url, url_encode(kw) )
            print("urlurlurl::",url)
            return werkzeug.utils.redirect(url)

        return 'false'