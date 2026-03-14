# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression
from bs4 import BeautifulSoup
import json

_logger = logging.getLogger(__name__)


class BlogPost(models.Model):
    _inherit = "blog.post"


    related_blog_product_ids = fields.Many2many(
        'product.template',
        'related_blog_rel',
        'blog_id', 'product_id',
        string='Related Blog')
    case_study_blog_product_ids = fields.Many2many(
        'product.template',
        'case_study_blog_rel',
        'blog_id', 'product_id',
        string='Case Study Blog Product')
    brand_id = fields.Many2one("product.brand","Brand")


    @api.model_create_multi
    def create(self, vals_list):
        blogs = super(BlogPost, self).create(vals_list)
        for blog in blogs:
            if blog.is_published:
                blog.sudo().send_email_new_post()
        return blogs

    def write(self, values):
        res = super(BlogPost, self).write(values)
        if values.get('is_published'):
            self.sudo().send_email_new_post()
        return res

    def send_email_new_post(self):
        for blog in self:
            website = blog.sudo().website_id
            template_email = website.sudo().template_blog_email_id
            if template_email:
                new_template = template_email.sudo().copy()
                name = new_template.sudo().subject+' ['+blog.name+']'
                body_html = new_template.sudo().body_html
                body_html = body_html.replace("blog title",blog.name)
                body_html = body_html.replace("/blog_url",blog.website_url)
                soup = BeautifulSoup(body_html)
                img_tag = soup.find(alt="blog_image")
                image_src = json.loads(blog.cover_properties)
                image_src = image_src['background-image']
                image_src = image_src.replace("url(","")
                image_src = image_src[:-1]
                body_html = body_html.replace(img_tag.get('src'),image_src)
                new_template.sudo().write({'preview':blog.name,'name':name,'body_html':body_html})
                new_template.sudo().action_put_in_queue()
        return True
