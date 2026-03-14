# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Location(models.Model):
    _inherit = "stock.location"

    is_sample_location = fields.Boolean('Sample Request Location', default=False)