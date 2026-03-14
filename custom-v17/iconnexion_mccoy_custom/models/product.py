# -*- coding: utf-8 -*-

import itertools
import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression


class ProductTemplate(models.Model):
	_inherit = "product.template"

	quotation_history_ids = fields.One2many('icon.quotation.history','product_tmpl_id', string="Quotation History")
	taxes_id = fields.Many2many('account.tax', 'product_taxes_rel', 'prod_id', 'tax_id', help="Default taxes used when selling the product.", string='Customer Taxes',
        domain=[('type_tax_use', '=', 'sale')], default=lambda self: self.env.company.company_customer_tax_product_id)
