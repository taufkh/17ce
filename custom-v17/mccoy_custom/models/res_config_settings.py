# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    template_blog_email_id = fields.Many2one("mailing.mailing","Template Blog Email",related="website_id.template_blog_email_id",readonly=False)
    email_submit_order_id = fields.Many2one("mail.template","Email Submit Order",related="website_id.email_submit_order_id",readonly=False)