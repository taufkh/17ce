from odoo import api, fields, models




class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    def_exp_product_id = fields.Many2one("product.product",related="company_id.def_exp_product_id", string='Default Expense Product',  readonly=False)



