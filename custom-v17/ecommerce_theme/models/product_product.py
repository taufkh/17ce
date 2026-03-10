# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)



class ProductProduct(models.Model):
    _inherit = "product.product"


    def ecomerce_rating(self):
    	rating = self.env.ref('website_sale.product_comment').active
    	return self.env["ir.ui.view"]._render_template('portal_rating.rating_widget_stars_static', values={
                            'rating_avg': self.rating_avg,
                            'rating_count': self.rating_count,
                        })