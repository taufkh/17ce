# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64

from odoo import api, fields, models, tools, _
from odoo.modules.module import get_module_resource

class OdesApprovalResult(models.Model):
    _inherit = 'approval.category'

    is_art_result = fields.Boolean(string='ART Test Result')