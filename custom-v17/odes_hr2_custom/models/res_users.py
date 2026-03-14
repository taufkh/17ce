from odoo import api,fields,models

class ResUsers(models.Model):
    _inherit = 'res.users'

    substitute_approver_ids = fields.Many2many('res.users', 'substitute_approver_user_rel', 'substitute_id', 'approver_id', "Approver Substitute")