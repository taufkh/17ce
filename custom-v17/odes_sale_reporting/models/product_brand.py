# -*- coding: utf-8 -*-
# v16: product.brand model moved here from ecommerce_theme/mccoy_custom
# (ecommerce_theme has heavy website deps; mccoy_custom is blocked for Community)
from odoo import fields, models


class ProductBrand(models.Model):
    _name = "product.brand"
    _description = "Product Brand"

    name = fields.Char('Name', required=True)
    description = fields.Text('Description')
    image = fields.Binary('Image')
    manufacturing_company_id = fields.Many2one('res.partner', string="Manufacturing Company")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_brand_id = fields.Many2one('product.brand', string="Brand")
