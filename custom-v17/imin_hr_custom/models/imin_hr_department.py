# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class IminHrDepartment(models.Model):
    _name = 'imin.hr.department'
    _description = 'iMin HR Departments'

    name = fields.Char('Name')
    parent_id = fields.Many2one('imin.hr.department', 'Parent')
    imin_id = fields.Integer('iMin ID')
    imin_parent_id = fields.Integer('iMin Parent ID')