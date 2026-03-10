
from datetime import datetime, timedelta
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import ast


class OdesCrmPiplineWizard(models.TransientModel):
    _name = "odes.crm.pipeline.wizard"
    _description = "CRM Pipeline Wizard"

    crm_team_id = fields.Many2one('crm.team', string='Sales Team')
    crm_stage_ids = fields.Many2many('crm.stage', 'team_rel_id', 'team_id', string='Stages')

    def action_continue(self):
        action = self.env["ir.actions.act_window"]._for_xml_id('crm.crm_lead_action_pipeline')

        context = self._context.copy()
        if 'context' in action and type(action['context']) == str:
            context.update(ast.literal_eval(action['context']))
        else:
            context.update(action.get('context', {}))
        action['context'] = context
        action['context'].update({
            'default_team_id': self.crm_team_id.id,
            'search_default_team_id': self.crm_team_id.id,
        })
        return action

    @api.onchange('crm_team_id')
    def _onchange_get_team_stage(self):
        self.crm_stage_ids = self.env['crm.stage'].search([]) if self.crm_team_id else False#self.crm_team_id.stage_ids
