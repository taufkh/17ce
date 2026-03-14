from odoo import api, fields, models

class OdesApplication(models.Model):
    _name = "odes.application"
    _description = "ODES Application"

    name = fields.Char('Application')
    name_small = fields.Char('Application New')
