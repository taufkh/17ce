# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class OdesCrmDocConfig(models.Model):
    _name = 'odes.crm.doc.config'
    _description = 'Documentation Configs'
    _order = 'sequence, id'

    @api.onchange('title_id')
    def _onchange_title_id(self):
        if self.title_id:
            self.name = self.title_id.name

    name = fields.Char('Name')
    title_id = fields.Many2one('odes.crm.doc.title', string='Title')
    company_id = fields.Many2one('res.company', string='Company')
    sequence = fields.Integer('Sequence', default=10)