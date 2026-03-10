
import logging
import threading
from datetime import date, datetime, timedelta
from psycopg2 import sql

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.osv import expression
from odoo.tools.translate import _
from odoo.tools import email_re, email_split
from odoo.exceptions import UserError, AccessError
from odoo.addons.phone_validation.tools import phone_validation
from collections import OrderedDict, defaultdict

class Team(models.Model):
    _inherit = 'crm.team'

    stage_ids = fields.One2many('crm.stage', 'team_id', 'Stages')

    new_member_ids = fields.Many2many('res.users', 'sale_team_id', string='Channel Members', check_company=True, domain=[('share', '=', False)], help="Add members to automatically assign their documents to this sales team. You can only be member of one team.")

    @api.model
    def action_your_pipeline(self):
        res = super(Team, self).action_your_pipeline()
        company = self.env.company
        res['domain'] = [('type','=','opportunity'), ('company_id', '=', company.id)]
        return res