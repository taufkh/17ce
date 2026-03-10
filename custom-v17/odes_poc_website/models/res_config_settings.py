# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    odes_is_active_cookies = fields.Boolean(related='website_id.odes_is_active_cookies', readonly=False)
    odes_button_text_cookies = fields.Char(related='website_id.odes_button_text_cookies', readonly=False)
    odes_message_title_cookies = fields.Char(related='website_id.odes_message_title_cookies', readonly=False)
    odes_message_cookies = fields.Text(related='website_id.odes_message_cookies', readonly=False)
    