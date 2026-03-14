
from datetime import datetime, timedelta
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import ast


class OdesCrmLeadHistoryWizard(models.TransientModel):
    _name = "odes.crm.lead.history.wizard"
    _description = "CRM Lead History Wizard"

    lead_id = fields.Many2one('crm.lead', string='CRM Lead', compute="_get_lead_id")
    possibility = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')], string='Possibility')
    history_reason = fields.Char('Reason')


    def _get_lead_id(self):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_id = context.get('active_id')

        if not active_model or not active_id:
            return

        if active_model == 'crm.lead':
            lead_obj = self.env['crm.lead']

            lead_search = lead_obj.search([('id', '=', active_id)])

            self.lead_id = lead_search

    def action_change_possibility(self):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_id = context.get('active_id')

        if not active_model or not active_id:
            return

        if active_model == 'crm.lead':
            lead_obj = self.env['crm.lead']
            lead_search = lead_obj.search([('id', '=', active_id)])
            history_obj = self.env['odes.crm.lead.history']

            lead_search.write({
                'possibility': self.possibility
                })

            history_obj.create({
                'lead_history_id': self.lead_id.id,
                'possibility': self.possibility,
                'history_reason': self.history_reason
                })
