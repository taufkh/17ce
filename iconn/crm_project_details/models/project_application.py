from odoo import fields, models


class CrmProjectApplication(models.Model):
    _name = 'crm.project.application'
    _description = 'Project Application'

    name = fields.Char(string='Application', required=True)
    active = fields.Boolean(default=True)
