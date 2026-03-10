# -*- encoding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.parser import parse


class ResUsers(models.Model):
    _inherit = "res.users"

    currency_ids = fields.Many2many('res.currency', 'users_currency_rel', 'user_id', 'currency_id', string='Currencies')
    user_code = fields.Char('Salesperson Code')
    so_sequence_id = fields.Many2one('ir.sequence', 'SO Sequence')

    is_finance = fields.Boolean('Finance')
    is_director = fields.Boolean('Director')

    timesheet_company_ids = fields.Many2many('res.company', 'timesheet_user_company_rel', 'user_id', 'company_id', string='Timesheet Companies')

    def write(self, vals):
        company = self.env.company
        company_code = company.company_code or 'MC'
        for user in self:
            if vals.get('user_code'):
                sequence_obj = self.env['ir.sequence']
                implementation = 'no_gap'
                padding = 3
                use_date_range = True
                range_reset = 'daily'

                seq_vals = {}
                if not user.so_sequence_id:
                    seq_vals = {
                        'implementation': implementation,
                        'padding': padding,
                        'use_date_range': use_date_range,
                        'range_reset': range_reset,
                    }

                seq_vals.update({
                    'name': vals['user_code']+' Sales Order',
                    'prefix': vals['user_code']+company_code+'%(y)s%(month)s%(day)s'
                })

                if not user.so_sequence_id:
                    so_sequence_id = sequence_obj.create(seq_vals).id

                    vals.update({
                        'so_sequence_id': so_sequence_id,
                    })
                else:
                    project.so_sequence_id.write(seq_vals)

        return super(ResUsers, self).write(vals)

    def _is_manager(self):
        return self.has_group('odes_custom.group_odes_manager')