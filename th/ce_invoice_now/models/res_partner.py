# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ce_applicable_invoicenow = fields.Boolean(string='Applicable for CE InvoiceNow?')
