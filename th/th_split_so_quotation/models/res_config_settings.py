from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    split_remove_qty = fields.Boolean(
        string='Remove Split quantity from SO / Quotation',
        config_parameter='th_split_so_quotation.remove_split_qty',
    )
