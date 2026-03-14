from odoo import api, fields, models

class ProductProduct(models.Model):
    _inherit = "product.product"

    mccoy_smart_iot_desc = fields.Char('Smart IOT Desc')