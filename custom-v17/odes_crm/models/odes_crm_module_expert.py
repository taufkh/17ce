# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class OdesCrmModuleExpert(models.Model):
    _name = 'odes.crm.module.expert'
    _description = 'Module Subject Expert'

    @api.onchange('module_id')
    def _onchange_module_id(self):
        if self.module_id:
            self.name = self.module_id.name

    name = fields.Char('Name')
    module_id = fields.Many2one('odes.crm.requirement.module', string='Module')
    expert_user_id = fields.Many2one('res.users', string='Subject Expert')
    order_id = fields.Many2one('sale.order', string='Order Reference')