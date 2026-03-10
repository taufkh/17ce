# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import html2plaintext
import math
from datetime import timedelta

class ResCompany(models.Model):
    _inherit = "res.company"

    company_chop = fields.Binary(string="Company Chop", groups="base.group_system")
    
    def action_recompute_payment_number(self):
        move_obj = self.env['account.move']
        moves = move_obj.search([('payment_id', '!=', False)])
        for move in moves:
            self.env.add_to_compute(move_obj._fields['sequence_prefix'], move)
            self.env.add_to_compute(move_obj._fields['sequence_number'], move)
            self.env.add_to_compute(move_obj._fields['name'], move)