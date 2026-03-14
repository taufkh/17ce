# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression




class Website(models.Model):
    _inherit = "website"

    is_website_mccoy = fields.Boolean("Website McCoy")
    template_blog_email_id = fields.Many2one("mailing.mailing","Template Blog Email")
    background_subs = fields.Binary("Background Subscribers")
    email_submit_order_id = fields.Many2one("mail.template","Email Submit Order")