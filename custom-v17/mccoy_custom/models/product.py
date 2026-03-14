# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression
from odoo.tools.translate import html_translate

_logger = logging.getLogger(__name__)



class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    manufacturing_company_id = fields.Many2one("res.partner","Manufacturing Company")


class McCoyProductMOQ(models.Model):
    _name = "mccoy.product.moq"
    _description = "McCoy Product MOQ"
    _order = 'min_qty asc'

    name = fields.Char("Name",compute='_compute_name', store=True)
    product_id = fields.Many2one("product.template",'Product')
    product_variant_id = fields.Many2one("product.product",'Product Variant')
    min_qty = fields.Float("Min Qty",digits='Product Unit of Measure',required=True)
    price_unit = fields.Float("Price Unit",required=True)



    def convert_price_unit(self,currency=False):
        currency_origin = self.env.user.company_id.currency_id
        if currency:
            price_unit = currency_origin._convert(
                self.price_unit,
                currency,
                self.env.company,
                fields.Date.context_today(self),
            )
        else:
            price_unit = self.price_unit
        return price_unit
    



    @api.depends('product_id','min_qty')
    def _compute_name(self):
        for data in self:
            name = '-'
            if data.product_id:
                name = data.product_id.name + ' ['+str(data.min_qty)+']'
            data.name = name


    @api.constrains('product_id', 'min_qty','price_unit')
    def _check_data(self):
        for data in self:
            if data.min_qty <= 0:
                raise ValidationError("Please, Input the correct min qty.")
            if data.price_unit <= 0:
                 raise ValidationError("Please, Input the correct price unit.")
            if data.product_id:
                if not data.product_variant_id:
                    self.env.cr.execute("select id from mccoy_product_moq where product_variant_id is null and product_id = %s and min_qty = %s  and id <> %s   limit 1", (data.product_id.id,data.min_qty,data.id))
                else:
                    self.env.cr.execute("select id from mccoy_product_moq where product_variant_id = %s and product_id = %s and min_qty = %s  and id <> %s   limit 1", (data.product_variant_id.id,data.product_id.id,data.min_qty,data.id))
                check = self.env.cr.fetchall() or False
                if check:
                    raise ValidationError("Min qty on MOQ'S can't be the same except the product variant on MOQ'S is different.")


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    is_mccoypublished = fields.Boolean("Publish On McCoy Components",default=True)

class ProductBrand(models.Model):
    _inherit = "product.brand"

    manufacturing_company_id = fields.Many2one('res.partner', string="Manufacturing Company")
    is_mccoypublished = fields.Boolean("Publish On McCoy Components",default=False)
    blog_id = fields.Many2one('blog.post','Blog')
    page_id = fields.Many2one("website.page","Page")
    key_search = fields.Char("Key Search")
    template_product = fields.Html("Template Product",sanitize_attributes=False, translate=html_translate, sanitize_form=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        brands = super(ProductBrand, self).create(vals_list)
        for brand in brands:
            if brand.name and not brand.key_search:
                brand.write({'key_search':brand.name})
        return brands

class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    volume = fields.Float("Volume")
    mpn = fields.Char('MPN',related='product_id.default_code')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        volume = 0
        if self.product_id:
            self.volume = self.product_id.volume
        else:
            self.volume = self.product_id.volume

class ProductTemplate(models.Model):
    _inherit = "product.template"


    product_brand_id = fields.Many2one('product.brand', string="Brand")
    manufacturing_company_id = fields.Many2one('res.partner', string="Manufacturing Company",related='product_brand_id.manufacturing_company_id')
    custom_tab_ids = fields.One2many('product.template.custom.tabs','product_id','Custom Tabs')
    related_blog_ids = fields.Many2many(
        'blog.post',
        'related_blog_rel',
        'product_id', 'blog_id',
        string='Related Blog')
    case_study_blog_ids = fields.Many2many(
        'blog.post',
        'case_study_blog_rel',
        'product_id', 'blog_id',
        string='Case Study Blog')
    sap_ref_no = fields.Char("SAP Ref No.")
    description_mpn = fields.Char("Description (MPN)")
    subcateg_id = fields.Many2one("product.category",'Subcategory')
    class_id = fields.Many2one("product.class",'Class')
    last_stock  = fields.Date("Last Stock")
    lead_time = fields.Datetime("Lead Time")
    avg_cost = fields.Monetary('AVG Cost')
    total_cost = fields.Monetary('Total Cost')
    moq_ids = fields.One2many("mccoy.product.moq","product_id","MOQ'S")
    currency_id = fields.Many2one(
        'res.currency', 'Currency', compute='_compute_currency_id')
    cost_currency_id = fields.Many2one(
        'res.currency', 'Cost Currency', compute='_compute_cost_currency_id')
    qty_multiply = fields.Integer("Qty Multiply")
    qty_multiply_info = fields.Char("Qty Multiply Information",inverse='_set_multiple_info', store=True)
    alternative_product_ids = fields.Many2many(
        'product.template', 'product_alternative_rel', 'src_id', 'dest_id', check_company=True,
        string='Related Products', help='Suggest alternatives to your customer (upsell strategy). '
                                            'Those products show up on the product page.')
    custom_length = fields.Float("Length",digits='Volume',inverse='_set_custom_length', store=True)
    custom_width = fields.Float("Width",digits='Volume',inverse='_set_custom_width',store=True)
    custom_height = fields.Float("Height",digits='Volume',inverse='_set_custom_height',store=True)
    volume = fields.Float('Volume', digits='Volume')
    custom_lead_time_by_weeks = fields.Char("Customer Lead Time (Weeks)", inverse='_set_lead_time_by_weeks', store=True)
    website_moq_price = fields.Float("Website Moq Price",compute="_compute_website_moq_price",store=True)


    def get_single_product_variant(self):
        """ Method used by the product configurator to check if the product is configurable or not.

        We need to open the product configurator if the product:
        - is configurable (see has_configurable_attributes)
        - has optional products (method is extended in sale to return optional products info)
        """
        self.ensure_one()
        result = super(ProductTemplate, self).get_single_product_variant()
        if self.product_variant_count == 1:
            return {
                'product_id': self.product_variant_id[0].id,
            }
        return result



    def write(self, vals):
        for p in self:
            dont_check = False
            if self._context.get("no_check_edit_ecommerce"):
                dont_check = True
            if len(vals)==1 and (vals.get('seller_ids') or vals.get('sale_history_ids')):
                dont_check = True
            if not dont_check:
                if not self.user_has_groups('mccoy_custom.group_mccoy_edit_product_ecommerce') and p.is_published:
                    raise ValidationError("Your user does not have access to edit ecommerce products.")
        res = super(ProductTemplate, self).write(vals)
        return res



    @api.depends('moq_ids','list_price')
    def _compute_website_moq_price(self):
        p_obj = self.env['product.product']
        company = self.env.company
        for template in self:
            website_moq_price = template.list_price
            product_variant_id = template.sudo()._get_first_possible_variant_id()
            if product_variant_id:
                website_moq_price = p_obj.browse(product_variant_id).get_min_price_product(company.currency_id)
            template.website_moq_price = website_moq_price

    @api.model_create_multi
    def create(self, vals_list):
        products = super(ProductTemplate, self).create(vals_list)
        for product in products:
            if product.product_brand_id.template_product:
                product.write({'website_description':product.product_brand_id.template_product})
        return products

    def set_desc_html_from_brand(self):
        for product in self:
            if product.product_brand_id.template_product:
                product.website_description = product.product_brand_id.template_product
        return True

    def get_min_qty(self):
        product = self
        min_qty = 0
        if product.moq_ids:
            min_qty = product.moq_ids.sorted(key=lambda line: (line.min_qty))[0].min_qty
        return int(min_qty)

    # def get_highest_price(self,currency):
    #     product = self
    #     highest_price = 0
    #     if product.moq_ids:
    #         highest_price = product.moq_ids.sorted(key=lambda line: (line.price_unit),reverse=True)[0].price_unit

    #     currency_origin = self.env.user.company_id.currency_id
    #     if currency:
    #         highest_price = currency_origin.compute(highest_price, currency)
    #     return highest_price


    # def get_lowest_price(self,currency):
    #     product = self
    #     lowest_price = 0
    #     if product.moq_ids:
    #         lowest_price = product.moq_ids.sorted(key=lambda line: (line.price_unit))[0].price_unit

    #     currency_origin = self.env.user.company_id.currency_id
    #     if currency:
    #         lowest_price = currency_origin.compute(lowest_price, currency)
    #     return lowest_price

    def get_min_price_product_in_template(self,product_id,currency):
        product_obj = self.env['product.product']
        price = product_obj.sudo().browse(product_id).get_min_price_product(currency)
        return price

    def get_min_qty_product_in_template(self,product_id):
        product_obj = self.env['product.product']
        qty = product_obj.sudo().browse(product_id).get_min_qty_product()
        return qty


    @api.onchange('custom_length','custom_width','custom_height')
    def _onchange_volume(self):
        volume = 0
        if self.custom_length and self.custom_width and self.custom_height:
            volume = self.custom_length * self.custom_width * self.custom_height
            self.volume = volume
        else:
            self.volume = volume
            
    def _set_lead_time_by_weeks(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.custom_lead_time_by_weeks = template.custom_lead_time_by_weeks

    def _set_multiple_info(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.qty_multiply_info = template.qty_multiply_info

    def _set_custom_length(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.custom_length = template.custom_length

    def _set_custom_width(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.custom_width = template.custom_width

    def _set_custom_height(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.custom_height = template.custom_height

    @api.model
    def default_get(self, fields):
        vals = super(ProductTemplate, self).default_get(fields)
        custom_tab_ids = [
        (0, 0,{'name':'Resources','sequence':1,'content_type':'custom'}),
                           (0, 0,{'name':'Details','sequence':2,'content_type':'custom'}),
                          (0, 0,{'name':'Inquiry','sequence':3,'content_type':'inquiry'}),
                          (0, 0,{'name':'Reviews','sequence':4,'content_type':'reviews'})
        ]
        vals['custom_tab_ids'] = custom_tab_ids

        return vals

    @api.depends('company_id')
    def _compute_currency_id(self):
        main_company = self.env['res.company']._get_main_company()
        for template in self:
            template.currency_id = template.company_id.sudo().currency_id.id or main_company.currency_id.id

    @api.depends_context('company')
    def _compute_cost_currency_id(self):
        self.cost_currency_id = self.env.company.currency_id.id

    def check_exist_tab(self):
        result = False
        for l in self.custom_tab_ids:
            if l.is_active:
                result = True
                break
        return result


    # def action_view_stock_move_lines(self):
    #     product_obj = self.env['product.template']
    #     products = product_obj.search([('is_published','=',True),('custom_tab_ids','!=',False),('product_brand_id','!=',False)])
    #     for product in products:
    #         edit_products = product_obj.search([('is_published','=',True),('custom_tab_ids','=',False)],limit=100)
    #         moq_ids = []
    #         public_categ_ids = []
    #         alternative_product_ids = []
    #         accessory_product_ids = []
    #         custom_tab_ids = []
    #         related_blog_ids = []
    #         case_study_blog_ids = []
    #         edit_products.moq_ids.unlink()
    #         edit_products.public_categ_ids.unlink()
    #         edit_products.alternative_product_ids.unlink()
    #         edit_products.accessory_product_ids.unlink()
    #         edit_products.custom_tab_ids.unlink()
    #         edit_products.related_blog_ids.unlink()
    #         edit_products.case_study_blog_ids.unlink()


    #         for moq in product.moq_ids:
    #             moq_ids.append((0, 0, {'min_qty':moq.min_qty,'price_unit':moq.price_unit}))
    #         for public_categ in product.public_categ_ids:
    #             public_categ_ids.append((4,public_categ.id))

    #         for alternative_product in product.alternative_product_ids:
    #             alternative_product_ids.append((4,alternative_product.id))

    #         for accessory_product in product.accessory_product_ids:
    #             accessory_product_ids.append((4,accessory_product.id))

    #         for custom_tab in product.custom_tab_ids:
    #             custom_tab_ids.append((0, 0, {
    #                 'name':custom_tab.name,
    #                 'content_type':custom_tab.content_type,
    #                 'sequence':custom_tab.sequence,
    #                 'content':custom_tab.content,
    #                 }))

    #         for related_blog in product.related_blog_ids:
    #             related_blog_ids.append((4,related_blog.id))

    #         for case_study_blog in product.case_study_blog_ids:
    #             case_study_blog_ids.append((4,case_study_blog.id))

    #         edit_products.write({
    #             'is_published':True,
    #             'qty_multiply':product.qty_multiply,
    #             'moq_ids':moq_ids,
    #             'list_price':product.list_price,
    #             'product_brand_id':product.product_brand_id.id,
    #             'image_1920':product.image_1920,
    #             'description_sale':product.description_sale,
    #             'public_categ_ids':public_categ_ids,
    #             'alternative_product_ids':alternative_product_ids,
    #             'accessory_product_ids':accessory_product_ids,
    #             'custom_tab_ids':custom_tab_ids,
    #             'related_blog_ids':related_blog_ids,
    #             'case_study_blog_ids':case_study_blog_ids,
    #         })


class ProductProduct(models.Model):
    _inherit = "product.product"
    
    lst_price = fields.Float(
        'Public Price', compute='_compute_product_lst_price',
        digits='Product Price', inverse='_set_product_lst_price',
        help="The sale price is managed from the product template. Click on the 'Configure Variants' button to set the extra attribute prices.")
    diff_variant_price = fields.Float("Diff Variants Price", digits='Product Price')
    custom_length = fields.Float("Length",digits='Volume')
    custom_width = fields.Float("Width",digits='Volume')
    custom_height = fields.Float("Height",digits='Volume')
    volume = fields.Float('Volume', digits='Volume')
    custom_lead_time_by_weeks = fields.Char("Customer Lead Time (Weeks)")
    qty_multiply_info = fields.Char("Packaging Info")


    def get_min_qty_product(self):
        product = self
        min_qty = 1
        if product.moq_ids:
            moq = product.product_tmpl_id.moq_ids.filtered(lambda line: line.product_variant_id==self or not line.product_variant_id)
            if moq:
                min_qty = moq.sorted(key=lambda line: (line.min_qty))[0].min_qty
        return int(min_qty)

    def get_min_price_product(self,currency):
        product = self
        price_unit = product.lst_price
        currency_origin = self.env.user.company_id.currency_id
        if product.moq_ids:
            moq = product.product_tmpl_id.moq_ids.filtered(lambda line: line.product_variant_id==self or not line.product_variant_id)
            if moq:
                new_moq = moq.sorted(key=lambda line: (line.min_qty))[0]
                min_qty = new_moq.min_qty
                price_unit = new_moq.price_unit
                if not new_moq.product_variant_id:
                    moq = product.product_tmpl_id.moq_ids.filtered(lambda line: line.product_variant_id==self)
                    if moq:
                        new_moq = moq.sorted(key=lambda line: (line.min_qty))[0]
                        if new_moq.min_qty == min_qty:
                            price_unit = new_moq.price_unit
        price_unit = currency_origin._convert(
            price_unit,
            currency,
            self.env.company,
            fields.Date.context_today(self),
        )
        return price_unit

    def get_actual_price(self,currency,qty):
        moq_obj = self.env['mccoy.product.moq']
        currency_origin = self.env.user.company_id.currency_id
        price = self.lst_price
        moqs = self.product_tmpl_id.moq_ids.filtered(lambda line: (line.product_variant_id==self or not line.product_variant_id) and line.min_qty<=qty)
        if moqs:
            new_moq = moqs.sorted(key=lambda line: (line.min_qty),reverse=True)[0]
            price = new_moq.price_unit
            min_qty = new_moq.min_qty
            price = new_moq.price_unit
            if not new_moq.product_variant_id:
                moqs = self.product_tmpl_id.moq_ids.filtered(lambda line: (line.product_variant_id==self) and line.min_qty<=qty)
                if moqs:
                    new_moq = moqs.sorted(key=lambda line: (line.min_qty),reverse=True)[0]
                    if new_moq.min_qty == min_qty:
                        price = new_moq.price_unit
        price = currency_origin._convert(
            price,
            currency,
            self.env.company,
            fields.Date.context_today(self),
        )

        return price

    def set_desc_html_from_brand(self):
        for product in self:
            if product.product_brand_id.template_product:
                product.website_description = product.product_brand_id.template_product
        return True


    @api.onchange('custom_length','custom_width','custom_height')
    def _onchange_volume(self):
        volume = 0
        if self.custom_length and self.custom_width and self.custom_height:
            volume = self.custom_length * self.custom_width * self.custom_height
            self.volume = volume
        else:
            self.volume = volume

    @api.depends('list_price', 'price_extra')
    @api.depends_context('uom')
    def _compute_product_lst_price(self):
        to_uom = None
        if 'uom' in self._context:
            to_uom = self.env['uom.uom'].browse(self._context['uom'])

        for product in self:
            if to_uom:
                list_price = product.uom_id._compute_price(product.list_price, to_uom)
            else:
                list_price = product.list_price
            if product.diff_variant_price:
                list_price = product.diff_variant_price
            product.lst_price = list_price + product.price_extra


    def _set_product_lst_price(self):
        for product in self:
            if self._context.get('uom'):
                value = self.env['uom.uom'].browse(self._context['uom'])._compute_price(product.lst_price, product.uom_id)
            else:
                value = product.lst_price
            value -= product.price_extra
            product.write({'diff_variant_price': value})


class ProductClass(models.Model):
    _name = "product.class"
    _description = "Product Class"


    name = fields.Char('Name', required=True)
    description = fields.Char('Description')



class ProductTemplateCustomTabs(models.Model):
    _name = "product.template.custom.tabs"
    _order = "sequence asc"
    _description = "Product Template Custom Tabs"


    name = fields.Char('Name', required=True)
    sequence = fields.Integer('Sequence', default=1, required=1)
    is_active = fields.Boolean('Active', default=True)
    content = fields.Html('Content')
    content_type = fields.Selection([
        ('custom', 'Custom'),
        ('reviews', 'Reviews Product'),
        ('inquiry', 'Inquiry'),
        ], string='Content Type', default='custom')
    product_id = fields.Many2one('product.template','Product')



class ProductTemplateMoqQty(models.Model):
    _name = "product.template.moq.qty"
    _description = "Product Template Moq Qty"


    name = fields.Char('Name', compute='_compute_name', store=True)
    moq_qty = fields.Integer('MOQ Qty')
    active = fields.Boolean('Active', default=True)
    price_unit = fields.Float('Price Unit', digits='Product Price')
    apply_on = fields.Selection([
        ('category', 'Category'),
        ('product', 'Product'),
        ], string='Apply On', default='category',required=1)
    categ_id = fields.Many2one("product.category","Category")
    product_id = fields.Many2one("product.template","Product")
    product_variant_id = fields.Many2one("product.product","Product Variant")
    pricelist_id = fields.Many2one("product.pricelist","Pricelist",required=False)
    price_line_ids = fields.One2many('product.template.moq.qty.price.lines','parent_id','Price Lines')


    @api.depends('categ_id','product_id','apply_on')
    def _compute_name(self):
        for data in self:
            name = '-'
            if data.apply_on == 'category':
                name = 'Category'
                if data.categ_id:
                    name+= ' ['+data.categ_id.name+']'
            if data.apply_on == 'product':
                name = 'Product'
                if data.product_id:
                    name+= ' ['+data.product_id.name+']'
            data.name = name

    @api.constrains('apply_on', 'categ_id','product_id')
    def _check_apply_on(self):
        data_obj = self.env['product.template.moq.qty']
        for data in self:
            if data.apply_on == 'category' and data.categ_id:
                self.env.cr.execute("select id from product_template_moq_qty where apply_on = %s and categ_id = %s  and id <> %s  limit 1", (data.apply_on,data.categ_id.id,data.id))
                check = self.env.cr.fetchall() or False
                if check:
                    raise ValidationError("Data Product Moq Qty already exists")
            if data.apply_on == 'product' and data.product_id:
                self.env.cr.execute("select id from product_template_moq_qty where apply_on = %s and product_id = %s and id <> %s  limit 1", (data.apply_on,data.product_id.id,data.id))
                check = self.env.cr.fetchall() or False
                if check:
                    raise ValidationError("Data Product Moq Qty already exists")



    @api.constrains('moq_qty')
    def _check_moq_qty(self):
        for data in self:
            if data.moq_qty <= 0 :
                raise ValidationError("Please input the correct moq qty.")


class ProductTemplateMoqQtyPriceLines(models.Model):
    _name = "product.template.moq.qty.price.lines"
    _description = "Product Template Moq Qty Price Lines"
    _order = "min_qty asc"

    name = fields.Char('Name', compute='_compute_name', store=True)
    pricelist_id = fields.Many2one("product.pricelist","Pricelist",required=True)
    price_unit = fields.Float('Price Unit', digits='Product Price')
    parent_id = fields.Many2one("product.template.moq.qty","Parent")
    min_qty = fields.Integer('Min Qty')


    @api.depends('pricelist_id','parent_id','price_unit')
    def _compute_name(self):
        for data in self:
            name = data.parent_id.name + ' [('+data.pricelist_id.name+') '+str(data.min_qty)+' - '+str(data.price_unit)+']'
            data.name = name


    @api.constrains('pricelist_id', 'min_qty')
    def _check_price_line(self):
        for data in self:
            self.env.cr.execute("select id from product_template_moq_qty_price_lines where pricelist_id = %s and min_qty = %s  and id <> %s and parent_id = %s  limit 1", (data.pricelist_id.id,data.min_qty,data.id,data.parent_id.id))
            check = self.env.cr.fetchall() or False
            if check:
                raise ValidationError("Data price line with min qty "+str(data.min_qty)+" " +data.pricelist_id.name+"  already exists in this MOQ configuration.")
            if data.min_qty <= 0:
                raise ValidationError("Please input the min qty value correctly.")
