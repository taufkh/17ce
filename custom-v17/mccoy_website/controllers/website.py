# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression




class Website(models.Model):
    _inherit = "website"


    def sale_product_domain(self):
        return [("sale_ok", "=", True),('type','!=','service')] + self.get_current_website().website_domain()


    def mccoy_blog(self):
        blog_obj = self.env['blog.post']
        blogs = blog_obj.search([('website_id','=',2),('is_published','=',True)])
        return blogs


    def get_image_blog(self,src):
        if src:
            src1 = src[4:]
            src = src1[:-2]
        return src

    def get_snippet_blog(self):
        data = []
        blogs = []
        brands = []
        blog_obj = self.env['blog.blog']
        brand_obj = self.env['product.brand']
        blogs = blog_obj.sudo().search_read(self.get_current_website().website_domain(),['name'])
        brands = brand_obj.sudo().search_read([('is_mccoypublished','=',True)],['name'])
        data.append(blogs)
        data.append(brands)
        return data