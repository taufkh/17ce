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


class PopularProductCarousel(http.Controller):
    @http.route(
        '/website/slider/popular_products',
        type='http',
        auth='public',
        methods=['GET'],
        website=True,
    )
    def get_popular_products(self, **kwargs):
        limit = kwargs.get('limit', 5)
        request.env.cr.execute(
            "SELECT pt.id, SUM(product_uom_qty) from sale_order_line so, product_product pp, product_template pt where so.product_id=pp.id and so.state != 'cancel' and pp.product_tmpl_id=pt.id and pt.is_published=True GROUP BY pt.id ORDER BY SUM(product_uom_qty) DESC limit %s" % (
                limit))

        product_ids = [product_data[0]
                       for product_data in request.env.cr.fetchall()]
        products = request.env['product.template'].sudo().browse(product_ids)

        popular_product_carousel = ""
        html_template = """
            <div class="item">
                <div class="item-img">
                    <img src="%s" height="77" width="77" alt=""/>
                    <div class="item-img-ho">

                     <a itemprop="url" href="%s"> 
                        <i class="fa fa-eye" title="View"/> 
                     </a>

                    </div>
                </div>
                <p><a itemprop="url" href="%s">%s</a></p>
                <strong>%s%s</strong>
            </div>                            
        """
        for product in products:
            product_link = 'shop/product/%s' % (product.id,)

            popular_product_carousel += html_template % (
                'web/image/product.template/' +
                str(product.id) + '/image_1024',
                product_link,
                product_link,
                product.name, round(product.list_price, 2),
                ' ' + request.website.get_current_pricelist().currency_id.symbol)

        response = request.make_response(popular_product_carousel)
        return response
