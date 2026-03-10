from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    is_delivery_method = fields.Boolean(string='Delivery Method')
