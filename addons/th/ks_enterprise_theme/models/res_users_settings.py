# -*- coding: utf-8 -*-
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResUsersSettings(models.Model):
    """
    Extend res.users.settings (community model) with:
    - color_scheme: per-user dark/light/system preference for Enterprise-style dark mode
    - homemenu_config: JSON storing the user's home menu app order
    """
    _inherit = 'res.users.settings'

    homemenu_config = fields.Json(
        string="Home Menu Configuration",
        readonly=True,
    )
    color_scheme = fields.Selection(
        [
            ('system', 'System'),
            ('light', 'Light'),
            ('dark', 'Dark'),
        ],
        default='system',
        required=True,
        string='Color Scheme',
    )
