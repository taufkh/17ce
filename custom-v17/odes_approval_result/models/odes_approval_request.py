# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class OdesApprovalRequest(models.Model):
    _inherit = 'approval.request'

    is_art_result = fields.Boolean(related='category_id.is_art_result')
    result = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string='Result', default=False)

    @api.onchange('name')
    def onchange_name(self):
        now = datetime.now()
        date_time = (now + timedelta(hours=8)).strftime("%d/%m/%Y")
        if self.is_art_result == True:                
           self.name = self.name + " (" + self.request_owner_id.name + ", " + str(date_time) + ")"
           self.date = now