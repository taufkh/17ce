##############################################################################
#
#       Copyright © SUREKHA TECHNOLOGIES PRIVATE LIMITED, 2020.
#
#       You can not extend,republish,modify our code,app,theme without our
#       permission.
#
#       You may not and you may not attempt to and you may not assist others
#       to remove, obscure or alter any intellectual property notices on the
#       Software.
#
##############################################################################
from odoo import http, fields,tools
from odoo.http import request
import json
from odoo.addons.http_routing.models.ir_http import slug, unslug
try:
    from odoo.addons.payment.controllers.portal import PaymentProcessing
except ImportError:
    from odoo.addons.payment.controllers.portal import PaymentPostProcessing

    class PaymentProcessing:
        @staticmethod
        def add_payment_transaction(transaction):
            PaymentPostProcessing.monitor_transactions(transaction)

        @staticmethod
        def remove_payment_transaction(transaction):
            PaymentPostProcessing.remove_transactions(transaction)
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers import main
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute
from odoo.addons.website_blog.controllers.main import WebsiteBlog
from odoo.addons.sale_product_configurator.controllers.main import ProductConfiguratorController
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from werkzeug.exceptions import Forbidden, NotFound
from odoo.addons.website_sale.controllers import main
from odoo.addons.web.controllers.main import Binary
from odoo.addons.web_editor.controllers.main import Web_Editor
import base64
import re
from dateutil.relativedelta import relativedelta
import werkzeug

class AuthSignupHome(AuthSignupHome):

    @http.route('/web/session/logout_redirect', type='http', auth="none")
    def logout_redirect(self, redirect='/web'):
        if request.session.get('return_url_reset_pass'):
            redirect = request.session['return_url_reset_pass']
        request.session.logout(keep_db=True)
        return werkzeug.utils.redirect(redirect, 303)

    @http.route()
    def web_auth_reset_password(self, *args, **kw):
        if request.session.uid:
            p = request.httprequest.base_url+'?'+str((request.httprequest.query_string).decode())
            request.session['return_url_reset_pass'] = p
            r = '/web/session/logout_redirect'
            return request.redirect(r)
        result = super(AuthSignupHome, self).web_auth_reset_password(*args, **kw)
        return result


class ProductConfiguratorController(ProductConfiguratorController):
    def _show_optional_products(self, product_id, variant_values, pricelist, handle_stock, **kw):
        product = request.env['product.product'].browse(int(product_id))
        combination = request.env['product.template.attribute.value'].browse(variant_values)
        get_min_qty = product.sudo().get_min_qty_product() or 1
        add_qty = int(kw.get('add_qty') or get_min_qty)
        if add_qty==1 and get_min_qty:
            add_qty = get_min_qty

        no_variant_attribute_values = combination.filtered(
            lambda product_template_attribute_value: product_template_attribute_value.attribute_id.create_variant == 'no_variant'
        )
        if no_variant_attribute_values:
            product = product.with_context(no_variant_attribute_values=no_variant_attribute_values)

        return request.env['ir.ui.view']._render_template("sale_product_configurator.optional_products_modal", {
            'product': product,
            'combination': combination,
            'add_qty': add_qty,
            'parent_name': product.name,
            'variant_values': variant_values,
            'pricelist': pricelist,
            'handle_stock': handle_stock,
        })


    # def _optional_product_items(self, product_id, pricelist, **kw):
    #     product = request.env['product.product'].browse(int(product_id))
    #     get_min_qty = product.sudo().get_min_qty_product() or 1
    #     add_qty = int(kw.get('add_qty') or get_min_qty)
    #     parent_combination = product.product_template_attribute_value_ids
    #     if add_qty==1 and get_min_qty:
    #         add_qty = get_min_qty
    #     if product.env.context.get('no_variant_attribute_values'):
    #         # Add "no_variant" attribute values' exclusions
    #         # They are kept in the context since they are not linked to this product variant
    #         parent_combination |= product.env.context.get('no_variant_attribute_values')

    #     return request.env['ir.ui.view']._render_template("sale_product_configurator.optional_product_items", {
    #         'product': product,
    #         'parent_name': product.name,
    #         'parent_combination': parent_combination,
    #         'pricelist': pricelist,
    #         'add_qty': add_qty,
    #     })


class Web_Editor(Web_Editor):

    @http.route('/web_editor/get_image_info', type='json', auth='user', website=True)
    def get_image_info(self, src=''):
        """This route is used to determine the original of an attachment so that
        it can be used as a base to modify it again (crop/optimization/filters).
        """
        attachment = None
        mccoy=False
        if 'mccoy' in src:
            mccoy = True
            id_match = re.search('^/mccoy/web/image/([^/?]+)', src)
        else:
            id_match = re.search('^/web/image/([^/?]+)', src)
        if id_match:
            url_segment = id_match.group(1)
            number_match = re.match('^(\d+)', url_segment)
            if '.' in url_segment: # xml-id
                attachment = request.env['ir.http']._xmlid_to_obj(request.env, url_segment)
            elif number_match: # numeric id
                if not mccoy:
                    attachment = request.env['ir.attachment'].browse(int(number_match.group(1)))
                else:
                    attachment = request.env['ir.attachment'].search([('mccoy_attach_id','=',int(number_match.group(1)))],limit=1)
        else:
            # Find attachment by url. There can be multiple matches because of default
            # snippet images referencing the same image in /static/, so we limit to 1
            attachment = request.env['ir.attachment'].search([('url', '=like', src)], limit=1)
        if not attachment:
            return {
                'attachment': False,
                'original': False,
            }
        return {
            'attachment': attachment.read(['id'])[0],
            'original': (attachment.original_id or attachment).read(['id', 'image_src', 'mimetype'])[0],
        }

class Home(http.Controller):

    # @http.route(['/landingpage'], type='http', auth='public', website=True)
    # def landingpage(self, **post):
    #     website_page_search_dom = [('view_id.arch_db', 'ilike', url)] + website.website_domain()
    #     pages = self.env['website.page'].search(website_page_search_dom)
    #     print(request.env['ir.http']._serve_page(),'aaaaaaaa')
    #     return super(Home, self).landingpage(**post)
    #     # return request.render('odes_landing_page.odes_intelligent_automation_page', values)

    

    @http.route(['/mccoy/web/image',
        '/mccoy/web/image/<string:xmlid>',
        '/mccoy/web/image/<string:xmlid>/<string:filename>',
        '/mccoy/web/image/<string:xmlid>/<int:width>x<int:height>',
        '/mccoy/web/image/<string:xmlid>/<int:width>x<int:height>/<string:filename>',
        '/mccoy/web/image/<string:model>/<int:id>/<string:field>',
        '/mccoy/web/image/<string:model>/<int:id>/<string:field>/<string:filename>',
        '/mccoy/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>',
        '/mccoy/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>/<string:filename>',
        '/mccoy/web/image/<int:id>',
        '/mccoy/web/image/<int:id>/<string:filename>',
        '/mccoy/web/image/<int:id>/<int:width>x<int:height>',
        '/mccoy/web/image/<int:id>/<int:width>x<int:height>/<string:filename>',
        '/mccoy/web/image/<int:id>-<string:unique>',
        '/mccoy/web/image/<int:id>-<string:unique>/<string:filename>',
        '/mccoy/web/image/<int:id>-<string:unique>/<int:width>x<int:height>',
        '/mccoy/web/image/<int:id>-<string:unique>/<int:width>x<int:height>/<string:filename>'], type='http', auth="public")
    def mccoy_content_image(self, xmlid=None, model='ir.attachment', id=None, field='datas',
                      filename_field='name', unique=None, filename=None, mimetype=None,
                      download=None, width=0, height=0, crop=False, access_token=None,
                      **kwargs):
        if id:
            model_obj = request.env['ir.attachment']
            data = model_obj.sudo().search([('mccoy_attach_id','=',int(id))],limit=1)
            id = data.id
        # other kwargs are ignored on purpose
        return self._mccoy_content_image(xmlid=xmlid, model=model, id=id, field=field,
            filename_field=filename_field, unique=unique, filename=filename, mimetype=mimetype,
            download=download, width=width, height=height, crop=crop,
            quality=int(kwargs.get('quality', 0)), access_token=access_token)

    def _mccoy_content_image(self, xmlid=None, model='ir.attachment', id=None, field='datas',
                       filename_field='name', unique=None, filename=None, mimetype=None,
                       download=None, width=0, height=0, crop=False, quality=0, access_token=None,
                       placeholder=None, **kwargs):
        status, headers, image_base64 = request.env['ir.http'].binary_content(
            xmlid=xmlid, model=model, id=id, field=field, unique=unique, filename=filename,
            filename_field=filename_field, download=download, mimetype=mimetype,
            default_mimetype='image/png', access_token=access_token)

        return Binary._content_image_get_response(
            status, headers, image_base64, model=model, id=id, field=field, download=download,
            width=width, height=height, crop=crop, quality=quality,
            placeholder=placeholder)


    # @http.route(['/mccoy/web/image/<string:dataid>/<string:random>'], type='http', auth="public")
    # def mccoy_web_content(self, dataid=None,random=None):
    #     if dataid:
    #         model_obj = request.env['ir.attachment']
    #         dataid = dataid.split('-')[0]
    #         data = model_obj.sudo().search([('mccoy_attach_id','=',int(dataid))],limit=1)
    #         content_file = base64.b64decode(data.datas)
    #         headers = [('Content-Type', data.mimetype), ('Content-Length', len(content_file))]
    #         response = request.make_response(content_file, headers=headers)
    #         return response


# class WebsiteBlog(WebsiteBlog):

#     def _prepare_blog_values(self, blogs, blog=False, date_begin=False, date_end=False, tags=False, state=False, page=False, search=None):
        
#         values_return = super(WebsiteBlog, self)._prepare_blog_values(blogs=blogs, blog=blog, date_begin=date_begin, date_end=date_end, tags=tags, state=state, page=page, search=search)
#         """ Prepare all values to display the blogs index page or one specific blog"""
#         if request.website.is_website_mccoy:
#             use_cover = request.website.is_view_active('website_blog.opt_blog_cover_post')
#             fullwidth_cover = request.website.is_view_active('website_blog.opt_blog_cover_post_fullwidth_design')
#             # if self.website_id.id
#             BlogPost = request.env['blog.post']
#             BlogTag = request.env['blog.tag']

#             # prepare domain
#             domain = values_return['domain']
#             domain+=[('related_blog_product_ids','=',False),('case_study_blog_product_ids','=',False)]
#             offset = (page - 1) * self._blog_post_per_page
#             first_post = BlogPost
#             if not blog:
#                 if use_cover and not fullwidth_cover:
#                     offset += 1
#             posts = BlogPost.search(domain, offset=offset, limit=self._blog_post_per_page, order="is_published desc, post_date desc, id asc")
#             total = BlogPost.search_count(domain)

#             pager = request.website.pager(
#                 url=request.httprequest.path.partition('/page/')[0],
#                 total=total,
#                 page=page,
#                 step=self._blog_post_per_page,
#             )
#             first_post = values_return['first_post']
#             post_ids = (first_post | posts).ids
#             values_return.update({
#                 'pager': pager,
#                 'posts': posts.with_prefetch(post_ids),
#                 'domain': domain,
#                 'blogs': blogs,
#                 'search_count': total,
#             }) 

#         return values_return


class MCCOYWebsite(WebsiteSale):

    def _get_mandatory_shipping_fields(self):
        return ["name","email", "street", "city", "country_id","zip"]


    @http.route([
        '/shop/submit',
    ], type='http', auth="public", website=True)
    def payment_submit(self, **post):
        order = False
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
        if order and sale_order_id:
            request.website.sale_reset()
            request.session['sale_last_order_id'] = False
            request.session['sale_order_id'] = False
            order.sudo().write({'is_dont_freight_account':True,'state':'sent'})
            template = request.website.sudo().email_submit_order_id
            if template:
                order.sudo().with_context(force_send=True).message_post_with_template(template.id)
            return request.render("mccoy_website.submit_order", {'order': order})
        else:
            return request.redirect('/shop')


    @http.route(['/shop/payment/transaction/',
        '/shop/payment/transaction/<int:so_id>',
        '/shop/payment/transaction/<int:so_id>/<string:access_token>'], type='json', auth="public", website=True)
    def payment_transaction(self, acquirer_id, save_token=False, order_id=None, access_token=None, token=None, **kwargs):
        """ Json method that creates a payment.transaction, used to create a
        transaction when the user clicks on 'pay now' button. After having
        created the transaction, the event continues and the user is redirected
        to the acquirer website.

        :param int acquirer_id: id of a payment.acquirer record. If not set the
                                user is redirected to the checkout page
        """
        # Ensure a payment acquirer is selected
        if not acquirer_id:
            return False

        try:
            acquirer_id = int(acquirer_id)
        except:
            return False

        # Retrieve the sale order
        if order_id:
            env = request.env['sale.order']
            domain = [('id', '=', order_id)]
            if access_token:
                env = env.sudo()
                domain.append(('access_token', '=', access_token))
            order = env.search(domain, limit=1)
        else:
            order = request.website.sale_get_order()

        # Ensure there is something to proceed
        if not order or (order and not order.order_line):
            return False

        assert order.partner_id.id != request.website.partner_id.id

        # Create transaction
        vals = {'acquirer_id': acquirer_id,
                'return_url': '/shop/payment/validate'}
        if order_id:
            vals['return_url'] = '/shop/payment/validate?sale_order_id='+str(order_id)

        if save_token:
            vals['type'] = 'form_save'
        if token:
            vals['payment_token_id'] = int(token)

        transaction = order._create_payment_transaction(vals)

        # store the new transaction into the transaction list and if there's an old one, we remove it
        # until the day the ecommerce supports multiple orders at the same time
        last_tx_id = request.session.get('__website_sale_last_tx_id')
        last_tx = request.env['payment.transaction'].browse(last_tx_id).sudo().exists()
        if last_tx:
            PaymentProcessing.remove_payment_transaction(last_tx)
        PaymentProcessing.add_payment_transaction(transaction)
        request.session['__website_sale_last_tx_id'] = transaction.id
        return transaction.render_sale_button(order)


    @http.route('/shop/payment/validate', type='http', auth="public", website=True, sitemap=False)
    def payment_validate(self, transaction_id=None, sale_order_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction. State at this point :

         - UDPATE ME
        """
        if sale_order_id is None:
            order = request.website.sale_get_order()
        else:
            sale_order_id = int(sale_order_id)
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            # assert order.id == request.session.get('sale_last_order_id')

        if transaction_id:
            tx = request.env['payment.transaction'].sudo().browse(transaction_id)
            assert tx in order.transaction_ids()
        elif order:
            tx = order.get_portal_last_transaction()
        else:
            tx = None

        if not order or (order.amount_total and not tx):
            return request.redirect('/shop')

        if order and not order.amount_total and not tx:
            order.with_context(send_email=True).action_confirm()
            return request.redirect(order.get_portal_url())

        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset()
        if tx and tx.state == 'draft':
            return request.redirect('/shop')

        PaymentProcessing.remove_payment_transaction(tx)
        return request.redirect('/shop/confirmation')

    @http.route(['/shop/payment'], type='http', auth="public", website=True, sitemap=False)
    def payment(self, **post):
        """ Payment step. This page proposes several payment means based on available
        payment.acquirer. State at this point :

         - a draft sales order with lines; otherwise, clean context / session and
           back to the shop
         - no transaction in context / session, or only a draft one, if the customer
           did go to a payment.acquirer website but closed the tab without
           paying / canceling
        """
        sale_obj = request.env['sale.order']
        order_pay = False
        order = request.website.sale_get_order()
        if post.get('id'):
            order = sale_obj.sudo().search([('id','=',post['id'])])
            if order:
                order_pay  =True
                request.session['sale_last_order_id'] = order.id
                request.session['__website_sale_last_tx_id'] = False

        if not order_pay:
            redirection = self.checkout_redirection(order)
            if redirection:
                return redirection

        render_values = self._get_shop_payment_values(order, **post)
        render_values['only_services'] = order and order.only_services or False

        if render_values['errors']:
            render_values.pop('acquirers', '')
            render_values.pop('tokens', '')
        if order_pay:
            
            render_values['order_id'] = order.id
            render_values['access_token'] = order.access_token
        return request.render("website_sale.payment", render_values)
            



    @http.route([
        '/shop/confirmation',
    ], type='http', auth="public", website=True)
    def payment_confirmation(self, **post):
        order = False
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
        if order and sale_order_id:
            # order._send_order_confirmation_mail()
            if order.freight_account_tmp:
                for line in order.order_line:
                    if line.is_delivery:
                        line.sudo().write({'name':line.name+'\n'+"Freight Account : "+order.freight_account_tmp})
            
        response = super(MCCOYWebsite, self).payment_confirmation(**post)
        return response


    @http.route(['/shop/<model("product.template"):product>'], type='http', auth="public", website=True, sitemap=True)
    def product(self, product, category='', search='', **kwargs):
        product_moq_qty_obj = request.env['product.template.moq.qty']
        product_moq_qty_price_obj = request.env['product.template.moq.qty.price.lines']

        if not product.can_access_from_current_website():
            raise NotFound()
        dict_data = self._prepare_product_values(product, category, search, **kwargs)
        pricelist_id = False
        moq_qty = False
        list_moq_price = product.moq_ids
        dict_data['list_moq_price'] = list_moq_price
        return request.render("website_sale.product", dict_data)


    @http.route(['/shop/subscribe'], type='http', auth="public", methods=['POST'], website=True)
    def subscribe(self, **post):
        subscribe_obj = request.env['mailing.contact']
        subcribers = subscribe_obj.search([('email', 'ilike', post.get('email'))])
        if not subcribers:
            subscribe_id = subscribe_obj.create({
                'email' : post.get('email'),
                'subscription_list_ids':[(0, 0, {
                        'list_id': request.env.ref('mass_mailing.mailing_list_data').id,
                    })]

            })

    @http.route()
    def shop(self, page=0, category=None, search='', brand='', ppg=False,
             **post):
        """
        Filter products by brand.
        """
        categ_obj = request.env['product.public.category']
        tmp_category_id = request.httprequest.cookies.get('categ_tmp_id') or False
        brand_tmps = request.httprequest.cookies.get('brand_tmp_ids') or False
        brand_tmps_value = False

        if tmp_category_id:
            category = categ_obj.sudo().browse(int(tmp_category_id))
        if brand_tmps:
            brand_tmps = brand_tmps.replace("brand=",'')
            brand_tmps = brand_tmps.split('&')
            brand_tmps_value = [int(x) for x in brand_tmps]
        if brand_tmps or tmp_category_id:
            page = 0


        response = super(MCCOYWebsite, self).shop(
            page=page, category=category, search=search, ppg=ppg, **post)

        # execute below block if url contains brand parameter
        brand_obj = request.env['product.brand']
        product_temp_obj = request.env['product.template']
        brands_list = request.httprequest.args.getlist('brand')
        if brand_tmps_value:
            brands_list = brand_tmps_value
        ppg, post = self.get_product_per_page(ppg, **post)
        domain, url = self.get_product_domain(search, category, post, response)
        if request.website.is_website_mccoy:
            domain += ['|',('company_id','=',request.website.company_id.id),('company_id','=',False)] 
            domain+=[('sale_ok','=',True),('website_published','=',True)]
        if brands_list:
            brand = self.get_product_brands(brands_list)
            if brand:
                attrib_list = request.httprequest.args.getlist('attrib')

                try:
                    brand_values = [int(x) for x in request.httprequest.args.getlist('brand')]
                except Exception as e:
                    brand_values = []

                if brand_tmps_value:
                    brand_values = brand_tmps_value

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
            'product_brands': brand_obj.sudo().search([('is_mccoypublished','=',True)], order='name asc'),
            'product_brand_set': set(brand_list),
            'search_count': product_count,
        }


        response.qcontext.update(values)
        return response


    @http.route('/inquiry-crm', type='json', auth='public')
    def inquiry_crm(self, product_id, name, phone, email, subject,company='',company_url='',question='',company_id=False):
        crm_obj = request.env['crm.lead']
        product_obj = request.env['product.template']
        product = product_obj.browse(int(product_id))
        if company_id:
            company_id = int(company_id)
        crm = crm_obj.sudo().create({
            'contact_name':name,
            'phone':phone,
            'email_from':email,
            'partner_name':company,
            'website':company_url,
            'name':subject,
            'description':question,
            'partner_id':request.env.user.partner_id.id,
            'user_id':request.env.user.id,
            'company_id':company_id,
            'type':'lead',
            'expected_revenue':product.list_price or 1,
            'product_id':product_id
        })


    @http.route('/get-actual-price-product', type='json', auth='public')
    def get_actual_price_product(self, product_id, currency_id, qty):
        crm_obj = request.env['crm.lead']
        product_obj = request.env['product.product']
        currency_obj = request.env['res.currency']
        curr = currency_obj.sudo().browse(currency_id)
        price = product_obj.sudo().browse(product_id).get_actual_price(curr,qty)
        return price

    @http.route('/get-history-sales-product', type='json', auth='public')
    def get_history_sales_product(self, product_id,cust_id=False):
        crm_obj = request.env['crm.lead']
        Monetary = request.env['ir.qweb.field.monetary']
        product_obj = request.env['product.product']
        currency_obj = request.env['res.currency']
        product = product_obj.sudo().browse(product_id)
        listsales = product.sale_order_line_ids
        if cust_id and listsales:
            listsales = listsales.filtered(lambda line: line.order_id.partner_id.id == cust_id)
        result = "<tbody>"
        count = 0
        for l in listsales:
            count+=1
            if count== 11:
                break
            date_order = l.order_id.date_order or ''
            if date_order:
                date_order = date_order + relativedelta(hours=8)
                date_order = date_order.strftime("%d-%m-%Y %H:%M:%S")
            price_unit = Monetary.value_to_html(l.price_unit, {'display_currency': l.order_id.currency_id})
            price_unit = price_unit.replace("oe_currency_value","")
            result+="""
                <tr>
                   <td>"""+date_order+"""</td>
                   <td>"""+l.order_id.name+"""</td>
                   <td>"""+(l.order_id.partner_id.display_name or '')+"""</td>
                   <td class="text-right">"""+price_unit+"""</td>
                </tr>
            """
        result+="</tbody>"
        return result

        


    @http.route('/get-actual-price-moq-product-change', type='json', auth='public')
    def get_actual_price_moq_product_change(self, product_id, currency_id):
        crm_obj = request.env['crm.lead']
        moq_obj = request.env['mccoy.product.moq']
        product_obj = request.env['product.product']
        currency_obj = request.env['res.currency']
        product = product_obj.sudo().browse(product_id)
        qty = product.qty_multiply
        curr = currency_obj.sudo().browse(currency_id)        
        min_qty = product.get_min_qty_product() or 1
        price = product.get_actual_price(curr,min_qty)
        code = product.default_code or ''
        return [price,min_qty,code]


    @http.route('/set-freight-account-order', type='json', auth='public')
    def set_freight_account_order(self, freight_account):
        order_obj = request.env['sale.order']
        moq_obj = request.env['mccoy.product.moq']
        product_obj = request.env['product.product']
        currency_obj = request.env['res.currency']
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = order_obj.sudo().browse(sale_order_id)
            order.sudo().write({'freight_account_tmp':freight_account})
        return True



