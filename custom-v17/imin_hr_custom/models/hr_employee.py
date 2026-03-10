# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    staff_id = fields.Char('Staff ID')
    member_id = fields.Char('Member ID')

class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    staff_id = fields.Char('Staff ID')
    member_id = fields.Char('Member ID')