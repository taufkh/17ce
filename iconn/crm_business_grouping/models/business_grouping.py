from odoo import fields, models


class BusinessGrouping(models.Model):
    _name = 'res.business.grouping'
    _description = 'Business Grouping'

    name = fields.Char(string='Grouping Name', required=True)
    code = fields.Char(string='Code', required=True)
    active = fields.Boolean(default=True)
