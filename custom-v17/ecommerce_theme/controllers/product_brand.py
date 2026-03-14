##############################################################################
#
#       Copyright © SUREKHA TECHNOLOGIES PRIVATE LIMITED, 2020.
#
#	    You can not extend,republish,modify our code,app,theme without our
#       permission.
#
#       You may not and you may not attempt to and you may not assist others
#       to remove, obscure or alter any intellectual property notices on the
#       Software.
#
##############################################################################
from odoo import http
from odoo.http import request

from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers import main
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute

main.PPG = 20  # Products Per Page
main.PPR = 3  # Products Per Row

class WebsiteProductBrand(WebsiteSale):

    def get_product_per_page(self, ppg=False, **post):
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = main.PPG
            post["ppg"] = ppg
        else:
            ppg = main.PPG
        return ppg, post

    def get_product_domain(self, search, category, post, response):
        attrib_values = response.qcontext['attrib_values']
        attrib_list = request.httprequest.args.getlist('attrib')
        url = "/shop"
        if search:
            post["search"] = search
        if category:
            category = request.env['product.public.category'].browse(
                int(category))
            url = "/shop/category/%s" % slug(category)
        if attrib_list:
            post['attrib'] = attrib_list

        domain = self._get_search_domain(
            search, category, attrib_values)

        return domain, url

    def get_product_brands(self, brand_ids):
        brand_obj = request.env['product.brand']
        product_brands = brand_obj.sudo().search(
            [('id', 'in', brand_ids)],
            order='name asc')
        return product_brands

    @http.route()
    def shop(self, page=0, category=None, search='', brand='', ppg=False,
             **post):
        """
        Filter products by brand.
        """
        response = super(WebsiteProductBrand, self).shop(
            page=page, category=category, search=search, ppg=ppg, **post)

        # execute below block if url contains brand parameter
        brand_obj = request.env['product.brand']
        product_temp_obj = request.env['product.template']
        brands_list = request.httprequest.args.getlist('brand')
        ppg, post = self.get_product_per_page(ppg, **post)
        domain, url = self.get_product_domain(search, category, post, response)

        if brands_list:
            brand = self.get_product_brands(brands_list)
            if brand:
                attrib_list = request.httprequest.args.getlist('attrib')

                try:
                    brand_values = [int(x) for x in request.httprequest.args.getlist('brand')]
                except Exception as e:
                    brand_values = []

                product_brands = brand_obj.sudo().browse(brand_values).exists()
                post["brand"] = brands_list

                domain += [('product_brand_id', 'in', product_brands.ids)]
                product_count = product_temp_obj.search_count(domain)
                pager = request.website.pager(
                    url=url, total=product_count, page=page, step=ppg,
                    scope=7, url_args=post)

                products = product_temp_obj.search(domain, limit=ppg,
                                                   offset=pager['offset'],
                                                   order=self._get_search_order(post))

                keep = QueryURL('/shop',
                                category=category and int(category),
                                search=search, brand=brands_list,
                                attrib=attrib_list, order=post.get('order'))

                values = {
                    'products': products,
                    'bins': TableCompute().process(products, ppg),
                    'pager': pager,
                    'search_count': product_count,
                    'search': search,
                    'product_brands': brand_obj.sudo().search([], order='name asc'),
                    'product_brand_set': set(brand_values),
                    'request_brands': brand,
                    'keep': keep,
                }
                response.qcontext.update(values)
                return response

        try:
            brand_list = [int(x) for x in request.httprequest.args.getlist('brand')]
        except Exception as e:
            brand_list = []

        product_count = product_temp_obj.search_count(domain)
        pager1 = request.website.pager(
            url=url, total=product_count, page=page, step=ppg,
            scope=7, url_args=post)
        products = product_temp_obj.search(domain, limit=ppg,
                                           offset=pager1['offset'],
                                           order=self._get_search_order(post))

        if products:
            product_brands = self.get_product_brands(products.mapped('product_brand_id').ids)
        else:
            product_brands = self.get_product_brands(brand_list)

        values = {
            'product_brands': product_brands,
            'product_brand_set': set(brand_list),
            'search_count': len(products),
        }

        response.qcontext.update(values)
        return response
