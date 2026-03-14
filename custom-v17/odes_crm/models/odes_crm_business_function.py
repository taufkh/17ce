# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class OdesCrmBusinessFunction(models.Model):
    _name = 'odes.crm.business.function'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Business Functions'

    name = fields.Char('Name', tracking=True)
    project_id = fields.Many2one('project.project', string='Project', tracking=True)
    order_id = fields.Many2one('sale.order', string='Order', tracking=True)
    requirement_ids = fields.One2many('odes.crm.requirement', 'business_function_id', string='Requirements')