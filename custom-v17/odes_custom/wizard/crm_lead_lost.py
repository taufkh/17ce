# -*- encoding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.parser import parse


class CrmLeadLost(models.TransientModel):
    _inherit = "crm.lead.lost"

    reason = fields.Char('Other Reason')
    is_input = fields.Boolean('Input', default=False)

    @api.onchange('lost_reason_id')
    def _onchange_lost_reason_id(self):
        if self.lost_reason_id:
            self.is_input = self.lost_reason_id.is_input
            if self.lost_reason_id.is_input:
                self.reason = False
            else:
                self.reason = self.lost_reason_id.name
        else:
            self.reason = False
            self.is_input = False

    def action_lost_reason_apply(self):
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        return leads.write({'lost_reason': self.reason, 'active': False, 'probability': 0,})