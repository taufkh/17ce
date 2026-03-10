# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import requests
import re

from odoo import models, fields, tools
from werkzeug.urls import url_join
from urllib.parse import urlsplit, urlunsplit

class SocialLivePostFacebook(models.Model):
    _inherit = 'social.live.post'

    def _post_facebook(self, facebook_target_id):
        self.ensure_one()
        account = self.account_id
        post_endpoint_url = url_join(self.env['social.media']._FACEBOOK_ENDPOINT, "/v3.3/%s/feed" % facebook_target_id)

        post = self.post_id

        # url_from_post = re.findall(tools.TEXT_URL_REGEX, post.message)

        # if url_from_post:
        #     url = url_from_post[0]
        #     url_split = urlsplit(url)
        #     base_url_from_post = url_split._replace(path='')
        #     message_with_shortened_urls = self.env['mail.render.mixin'].sudo()._shorten_links_text(post.message, self._get_utm_values(), base_url=base_url_from_post)
        # else:
        #     message_with_shortened_urls = self.env['mail.render.mixin'].sudo()._shorten_links_text(post.message, self._get_utm_values())
        # message_with_shortened_urls = self.env['mail.render.mixin'].sudo()._shorten_links_text(post.message, self._get_utm_values())
        message_with_shortened_urls = post.message

        params = {
            'message': message_with_shortened_urls,
            'access_token': account.facebook_access_token
        }

        if post.image_ids and len(post.image_ids) == 1:
            # if you have only 1 image, you have to use another endpoint with different parameters...
            params['caption'] = params['message']
            photos_endpoint_url = url_join(self.env['social.media']._FACEBOOK_ENDPOINT, '/v3.3/%s/photos' % facebook_target_id)
            image = post.image_ids[0]
            result = requests.request('POST', photos_endpoint_url, params=params,
                files={'source': ('source', open(image._full_path(image.store_fname), 'rb'), image.mimetype)})
        else:
            if post.image_ids:
                images_attachments = post._format_images_facebook(facebook_target_id, account.facebook_access_token)
                if images_attachments:
                    for index, image_attachment in enumerate(images_attachments):
                        params.update({'attached_media[' + str(index) + ']': json.dumps(image_attachment)})

            link_url = self.env['social.post']._extract_url_from_message(message_with_shortened_urls)
            # can't combine with images
            if link_url and not post.image_ids:
                params.update({'link': link_url})

            result = requests.post(post_endpoint_url, params)

        if (result.status_code == 200):
            self.facebook_post_id = result.json().get('id', False)
            values = {
                'state': 'posted',
                'failure_reason': False
            }
        else:
            values = {
                'state': 'failed',
                'failure_reason': json.loads(result.text or '{}').get('error', {}).get('message', '')
            }

        self.write(values)
