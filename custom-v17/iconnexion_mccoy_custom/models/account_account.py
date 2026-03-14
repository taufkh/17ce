from odoo import api, fields, models, _

class Account(models.Model):
    _inherit = "account.account"
    
    is_clearing = fields.Boolean(string='Is Clearing Account', default=False)