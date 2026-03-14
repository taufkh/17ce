# -*- coding: utf-8 -*-
import requests
from odoo import models, fields, api
from werkzeug.urls import url_encode, url_join


class OdesSocialMediaWebhooks(models.Model):
    _name = 'odes.social.media.webhooks'
    _description = 'odes social media webhooks'
    _order = 'sequence asc'

    name = fields.Char("Name")
    sequence = fields.Integer("Sequence", default=1)
    active = fields.Boolean("Active", default=True)
    callback_url = fields.Char("Callback Url")
    media_type = fields.Selection([
        ('facebook','Facebook'),
        ('instagram', 'Instagram'),
        ('facebook_account_callback_redirect','Facebook Account Callback Redirect Helper'),
        ], string='Media Type')
