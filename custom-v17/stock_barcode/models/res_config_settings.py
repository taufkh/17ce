from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    stock_barcode_use_form_handler = fields.Boolean(
        string='Open Barcode Scan in Form View',
        config_parameter='stock_barcode.use_form_handler',
        help='If enabled, barcode scan opens the standard picking form instead of a client action.',
    )

