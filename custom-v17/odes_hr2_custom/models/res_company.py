from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ResCompany(models.Model):
    _inherit = "res.company"

    def_exp_product_id = fields.Many2one("product.product","Default Expense Product")