# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.onchange('name')
    def _onchange_name(self):
        if self.user_id != False:
            user = self.env['res.users'].search([('id','=',self.user_id.id)])
            user.update({'name':self.name})

    @api.onchange('singaporean','pr_date')
    def _onchange_foreign_worker_levy(self):
        if self.singaporean or self.pr_date != False:
            self.factors = self.type_tiers = self.sectors = False

class HRLeave(models.Model):
    _inherit = "hr.leave"

    attachment = fields.Binary(string="Attachment File")
    attachment_name = fields.Char(string="Attachment Filename")

class HREmployeeUpdate(models.Model):
    _name = "hr.employee.update"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "HR Employee Update"

    name = fields.Char(string='Employee Name')
    employee_id = fields.Many2one('hr.employee')
    department_id = fields.Many2one('hr.department',string='Department')
    work_email = fields.Char(string='Work Email')
    state = fields.Selection([
        ('draft','Draft'),
        ('request','Request'),
        ('done','Done'),
    ], string='State', default='draft')
    message_main_attachment_id = fields.Many2one(groups="hr.group_hr_user")

    # educational information
    education_info_line = fields.One2many('hr.education.information','employee_update_id', string='Education Info Line')

    # other information
    dialect = fields.Char(string='Dialect')
    driving_licence = fields.Char(string='Driving Licence Class')
    car = fields.Boolean(string='Do you own a car?')
    resume = fields.Binary(string='Resume')
    employee_type_id = fields.Many2one('employee.id.type',string='Type Of ID')

    # dependents
    spouse_name = fields.Char(string='Spouse Name')
    spouse_nationality = fields.Many2one('res.country',string='Nationality')
    spouse_ident_no = fields.Char(string='Identification Number')
    spouse_dob = fields.Date(string='Spouse Date of Birth')
    marriage_date = fields.Date(string='Date of Marriage')
    dependent_ids = fields.One2many('dependents','employee_update_id')

    # training workshop
    training_ids = fields.One2many('employee.training','employee_update_id')

    # extra information
    physical_stability = fields.Boolean(string='Physical Disability (Yes)')
    physical_stability_no = fields.Boolean(string='Physical Disability (No)')
    physical = fields.Text(string='Physical Stability Information')
    court_b = fields.Boolean(string='Court (Yes)')
    court_no = fields.Boolean(string='Court (No)')
    court = fields.Text(string='Court Information')
    dismissed_b = fields.Boolean(string='Dismissed (Yes)')
    dismissed_no = fields.Boolean(string='Dismissed (No)')
    dismiss = fields.Text('Dismissed Information')
    bankrupt_b = fields.Boolean(string='Bankrupt (Yes)')
    bankrupt_no = fields.Boolean(string='Bankrupt (No)')
    bankrupt = fields.Text(string='Banckrupt Information')
    about = fields.Text('About')

    # private information
    # private contact
    address_home_id = fields.Many2one('res.partner', string='Address')
    emp_country_id = fields.Many2one('res.country', string='Country')
    emp_state_id = fields.Many2one('res.country.state', string='Residential State')
    emp_city_id = fields.Many2one('employee.city', string='City')
    private_email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    
    # citizenship
    country_id = fields.Many2one('res.country',string='Nationality (Country)')
    identification_id = fields.Char(string='Identification No')
    passport_id = fields.Char(string='Passport No')
    gender = fields.Selection([('male','Male'),('female','Female'),('other','Other')], string='Gender')
    birthday = fields.Date(string='Date of Birth')
    place_of_birth = fields.Char(string='Place of Birth')
    country_of_birth = fields.Many2one('res.country', string='Country of Birth')

    # emergency
    emergency_contact = fields.Char(string='Emergency Contact')
    emergency_phone = fields.Char(string='Emergency Phone')

    # education
    certificate = fields.Selection([
        ('graduate', 'Graduate'),
        ('bachelor','Bachelor'),
        ('master', 'Master'),
        ('doctor','Doctor'),
        ('other', 'Other')
    ], string='Certificate Level')
    study_field = fields.Char(string='Field of Study')
    study_school = fields.Char(string='School')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.name = self.employee_id.name
            self.department_id = self.employee_id.department_id
            self.work_email = self.employee_id.work_email
            self.education_info_line = self.employee_id.education_info_line
            self.dialect = self.employee_id.dialect
            self.driving_licence = self.employee_id.driving_licence
            self.car = self.employee_id.car
            self.resume = self.employee_id.resume
            self.employee_type_id = self.employee_id.employee_type_id
            self.spouse_name = self.employee_id.spouse_name
            self.spouse_nationality = self.employee_id.spouse_nationality
            self.spouse_ident_no = self.employee_id.spouse_ident_no
            self.spouse_dob = self.employee_id.spouse_dob
            self.marriage_date = self.employee_id.marriage_date
            self.dependent_ids = self.employee_id.dependent_ids
            self.training_ids = self.employee_id.training_ids
            self.physical_stability = self.employee_id.physical_stability
            self.physical_stability_no = self.employee_id.physical_stability_no
            self.court_b = self.employee_id.court_b
            self.court_no = self.employee_id.court_no
            self.dismissed_b = self.employee_id.dismissed_b
            self.dismissed_no = self.employee_id.dismissed_no
            self.bankrupt_b = self.employee_id.bankrupt_b
            self.bankrupt_no = self.employee_id.bankrupt_no
            self.about = self.employee_id.about
            self.address_home_id = self.employee_id.address_home_id
            self.emp_country_id = self.employee_id.emp_country_id
            self.emp_state_id = self.employee_id.emp_state_id
            self.emp_city_id = self.employee_id.emp_city_id
            self.private_email = self.employee_id.private_email
            self.phone = self.employee_id.phone
            self.country_id = self.employee_id.country_id
            self.identification_id = self.employee_id.identification_id
            self.passport_id = self.employee_id.passport_id
            self.gender =  self.employee_id.gender
            self.birthday = self.employee_id.birthday
            self.place_of_birth = self.employee_id.place_of_birth
            self.country_of_birth = self.employee_id.country_of_birth
            self.emergency_contact = self.employee_id.emergency_contact
            self.emergency_phone = self.employee_id.emergency_phone
            self.certificate = self.employee_id.certificate
            self.study_field = self.employee_id.study_field
            self.study_school = self.employee_id.study_school
        else:
            self.name = False
            self.department_id = False
            self.work_email = False
            self.education_info_line = False
            self.dialect = False
            self.driving_licence = False
            self.car = False
            self.resume = False
            self.employee_type_id = False
            self.spouse_name = False
            self.spouse_nationality = False
            self.spouse_ident_no = False
            self.spouse_dob = False
            self.marriage_date = False
            self.dependent_ids = False
            self.training_ids = False
            self.physical_stability = False
            self.physical_stability_no = False
            self.court_b = False
            self.court_no = False
            self.dismissed_b = False
            self.dismissed_no = False
            self.bankrupt_b = False
            self.bankrupt_no = False
            self.about = False
            self.address_home_id = False
            self.emp_country_id = False
            self.emp_state_id = False
            self.emp_city_id = False
            self.private_email = False
            self.phone = False
            self.country_id = False
            self.identification_id = False
            self.passport_id = False
            self.gender =  False
            self.birthday = False
            self.place_of_birth = False
            self.country_of_birth = False
            self.emergency_contact = False
            self.emergency_phone = False
            self.certificate = False
            self.study_field = False
            self.study_school = False
    
    def action_request(self):
        self.state = 'request'
        user_now = self.env.user
        users = self.env.ref('hr.group_hr_manager').users
        self.env.user
        for user in users:
            self.activity_schedule('odes_sign.mail_activity_data_odes_update_employee_data', user_id=user.id, note=f'''{user_now.name} request for update {self.name}'s employee data''')
    
    def action_approve(self):
        employee = self.env['hr.employee'].search([('id','=',self.employee_id.id)])
        result = employee.write({
            'name' : self.name,
            'work_email' : self.work_email,
            'education_info_line' : self.education_info_line,
            'dialect' : self.dialect,
            'driving_licence' : self.driving_licence,
            'car' : self.car,
            'resume' : self.resume,
            'employee_type_id' : self.employee_type_id,
            'spouse_name' : self.spouse_name,
            'spouse_nationality' : self.spouse_nationality,
            'spouse_ident_no' : self.spouse_ident_no,
            'spouse_dob' : self.spouse_dob,
            'marriage_date' : self.marriage_date,
            'dependent_ids' : self.dependent_ids,
            'training_ids' : self.training_ids,
            'physical_stability' : self.physical_stability,
            'physical_stability_no' : self.physical_stability_no,
            'court_b' : self.court_b,
            'court_no' : self.court_no,
            'dismissed_b' : self.dismissed_b,
            'dismissed_no' : self.dismissed_no,
            'bankrupt_b' : self.bankrupt_b,
            'bankrupt_no' : self.bankrupt_no,
            'about' : self.about,
            'address_home_id' : self.address_home_id,
            'emp_country_id' : self.emp_country_id,
            'emp_state_id' : self.emp_state_id,
            'emp_city_id' : self.emp_city_id,
            'private_email' : self.private_email,
            'phone' : self.phone,
            'country_id' : self.country_id,
            'identification_id' : self.identification_id,
            'passport_id' : self.passport_id,
            'gender' :  self.gender,
            'birthday' : self.birthday,
            'place_of_birth' : self.place_of_birth,
            'country_of_birth' : self.country_of_birth,
            'emergency_contact' : self.emergency_contact,
            'emergency_phone' : self.emergency_phone,
            'certificate' : self.certificate,
            'study_field' : self.study_field,
            'study_school' : self.study_school,
        })
        self.state = 'done'

        activity_id = self.env['mail.activity'].search([('res_id','=',self.id),('user_id','=',self.env.user.id),('activity_type_id','=',self.env.ref('odes_sign.mail_activity_data_odes_update_employee_data').id)])
        activity_id.action_feedback(feedback='Approve')
        other_activity_ids = self.env['mail.activity'].search([('res_id','=',self.id),('activity_type_id','=',self.env.ref('odes_sign.mail_activity_data_odes_update_employee_data').id)])
        other_activity_ids.unlink
        self.sudo()._get_user_approval_activities_unlink()
        return result
    
    def _get_user_approval_activities_unlink(self):
        group = self.env.ref('hr.group_hr_manager').users.ids
        for user in group:
            domain = [
                ('res_model', '=', 'hr.employee.update'),
                ('res_id', 'in', self.ids),
                ('activity_type_id', '=', self.env.ref('odes_sign.mail_activity_data_odes_update_employee_data').id),
                ('user_id', '=', user)
            ]
            activities = self.env['mail.activity'].search(domain)
            activities.unlink()
        return activities

class HrEducationInformation(models.Model):
    _inherit = "hr.education.information"

    employee_update_id = fields.Many2one('hr.employee.update', string='Update ID')

class Dependents(models.Model):
    _inherit = "dependents"

    employee_update_id = fields.Many2one('hr.employee.update', string='Update ID')

class EmployeeTraining(models.Model):
    _inherit = "employee.training"

    employee_update_id = fields.Many2one('hr.employee.update', string='Update ID')
