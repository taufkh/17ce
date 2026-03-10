from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    spouse_name = fields.Char("Spouse Name")
    spouse_dob = fields.Date("Spouse Date of Birth")
    spouse_ident_no = fields.Char("Identification number")
    marriage_date = fields.Date("Date of Marriage")
    spouse_nationality = fields.Many2one('res.country', "Nationality")

    @api.constrains('spouse_dob')
    def _check_spouse_dob(self):
        for rec in self:
            today = datetime.today().date()
            if rec.spouse_dob:
                if rec.spouse_dob > today:
                    raise ValidationError(
                        "Please enter valid Date of Birth for spouse")
            return True


class Dependents(models.Model):
    _inherit = "dependents"

    gender = fields.Selection([('male', 'Male'),
                               ('female', 'Female')],
                              "Gender")
