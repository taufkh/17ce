
from datetime import datetime, timedelta
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import ast


class OdesCrmBackwardStageWizard(models.TransientModel):
    _name = "odes.crm.backward.stage.wizard"
    _description = "CRM Backward Stage Wizard"

    lead_id = fields.Many2one('crm.lead', string='CRM Lead', compute="_get_lead_id")
    stage_id = fields.Many2one('crm.stage', 'Stage')
    stage_sequence = fields.Integer('Sequence')
    lead_team_id = fields.Many2one('crm.team', string='Sales Team')
    reason = fields.Char('Reason')
    company_id = fields.Many2one('res.company', string='Company')

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
            self.lead_team_id = lead_search.team_id

            for lead_seq in lead_search.stage_id:
                stage_obj = self.env['crm.stage'].search([('sequence', '<' , lead_seq.sequence )])
                stage_get = self.env['crm.stage'].browse(stage_obj)

                self.stage_sequence = lead_search.stage_id.sequence
                self.company_id = lead_search.company_id.id

    def action_change_stage(self):
        if self.stage_id == self.lead_id.stage_id:
            raise UserError(_('Sorry, the stage cannot be the same as the previous stage'))

        if not self.stage_id == self.lead_id.stage_id:
            self.lead_id.with_context({'odes_view': 1,}).write({
                'stage_id': self.stage_id.id
                })



            return self.write_to_history()

    def write_to_history(self):
        odes_stage_obj = self.env['odes.crm.stage']
        last_stage = odes_stage_obj.search([('lead_id', '=', self.lead_id.id)], order='start_datetime desc', limit=1)

        last_stage.write({
            'backward_reason':self.reason
            })
