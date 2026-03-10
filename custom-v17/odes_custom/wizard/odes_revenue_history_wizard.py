
from datetime import datetime, timedelta
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import ast


class OdesRevenueHistoryWizard(models.TransientModel):
    _name = "odes.revenue.history.wizard"
    _description = "Revenue History Wizard"

    lead_id = fields.Many2one('crm.lead', string='CRM Lead', compute="_get_lead_id")
    amount = fields.Monetary('Amount')
    change_reason = fields.Char('Reason')
    currency_id = fields.Many2one('res.currency', 'Currency')

    def _get_lead_id(self):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_id = context.get('active_id')

        if not active_model or not active_id:
            return

        if active_model == 'crm.lead':
            lead_obj = self.env['crm.lead']

            lead_search = lead_obj.search([('id', '=', active_id)])

            self.lead_id = lead_search.id
            # self.currency_id = lead_search.currency_id.id

    @api.model
    def default_get(self, fields):
        defaults = super(OdesRevenueHistoryWizard, self).default_get(fields)

        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_id = context.get('active_id')

        if active_id and active_model == 'crm.lead':
            lead_obj = self.env['crm.lead']
            lead_search = lead_obj.search([('id', '=', active_id)])

            defaults['amount'] = lead_search.currency_revenue
            defaults['currency_id'] = lead_search.currency_id.id

        return defaults

    def action_change_revenue(self):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_id = context.get('active_id')

        if not active_model or not active_id:
            return

        if active_model == 'crm.lead':
            lead_obj = self.env['crm.lead']
            lead_search = lead_obj.search([('id', '=', active_id)])
            history_obj = self.env['odes.revenue.history']

            lead_search.write({
                'currency_revenue': self.amount,
                'currency_id': self.currency_id.id,
                })
            lead_search._onchage_revenue()

            history_obj.create({
                'crm_lead_revenue_history_id': lead_search.id,
                'amount': self.amount,
                'change_reason': self.change_reason
                })
