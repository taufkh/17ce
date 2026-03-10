# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class IminHrEmployee(models.Model):
    _name = 'imin.hr.employee'
    _description = 'iMin HR Employees'

    # Basic Fields
    name = fields.Char('Name')
    department_id = fields.Many2one('imin.hr.department', 'Department')
    email = fields.Char('Email')
    date = fields.Date('Employment Date')
    member_type = fields.Selection([('1', 'Full Time'), ('2', 'Part Time'), ('3', 'Internship'), ('4', 'Contractor'), ('5', 'Rehire After Retirement'), ('6', 'Outsourced Employee')], string='Employment Type')
    mobile = fields.Char('Mobile')
    gender = fields.Selection([('1', 'Male'), ('2', 'Female'), ('3', 'Secret')], string='Gender')
    pic = fields.Binary('Image')
    position = fields.Char('Designation')
    tel_area_code = fields.Char('Country Code')

    # Technical Fields
    imin_id = fields.Integer('iMin ID')
    imin_org_id = fields.Integer('iMin Organization ID')
    imin_department_id = fields.Integer('iMin Department ID')
    ext_number = fields.Char('Extension Number')
    staff_id = fields.Char('Staff ID')
    org_queue = fields.Char('Department Level')
    imin_create_time = fields.Datetime('iMin Create Time')
    imin_update_time = fields.Datetime('iMin Update Time')