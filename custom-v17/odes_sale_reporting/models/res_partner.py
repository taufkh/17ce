# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_code = fields.Char('Customer Code')