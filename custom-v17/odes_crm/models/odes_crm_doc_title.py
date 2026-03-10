# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class OdesCrmDocTitle(models.Model):
    _name = 'odes.crm.doc.title'
    _description = 'Documentation Titles'

    name = fields.Char('Name')