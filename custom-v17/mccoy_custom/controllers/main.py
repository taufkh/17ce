from odoo import http, fields
from odoo.http import request
import json
from odoo.tools.misc import xlsxwriter
from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers import main
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute
from odoo.addons.website_blog.controllers.main import WebsiteBlog
from odoo.addons.sale_product_configurator.controllers.main import ProductConfiguratorController
from werkzeug.exceptions import Forbidden, NotFound
from odoo.addons.website_sale.controllers import main
from odoo.addons.web.controllers.main import Binary
from odoo.addons.web_editor.controllers.main import Web_Editor
import base64
import re
import io


class MccoyCustom(http.Controller):


    @http.route('/web/export_product_xlsx', type='http', auth='user')
    def export_product_xlsx(self, **post):
        wizard_obj = request.env['mccoy.special.export.wizard']
        data_id = int(post.get('data_id'))

        wizard = wizard_obj.browse(data_id)
        if wizard.product_template_ids:
            data_obj = 'product.template'
            data_obj1 = 'product_template'
            products = wizard.product_template_ids
        elif wizard.product_ids:
            data_obj = 'product.product'
            data_obj1 = 'product_product'
            products = wizard.product_ids

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(data_obj)
        style_highlight = workbook.add_format({'bold': True, 'pattern': 1, 'bg_color': '#E0E0E0', 'align': 'center'})
        style_normal = workbook.add_format({'align': 'center'})
        format_minititle_center = workbook.add_format({'font_size': 12, 'align': 'left'})
        row = 0
        worksheet.set_column(0, 25, 30)
        worksheet.write(row, 0, 'id',format_minititle_center)
        worksheet.write(row, 1, 'variant_seller_ids/id',format_minititle_center)
        worksheet.write(row, 2, 'moq_ids/id',format_minititle_center)

        worksheet.write(row, 3, 'default_code',format_minititle_center)
        worksheet.write(row, 4, 'name',format_minititle_center)
        worksheet.write(row, 5, 'product_brand_id',format_minititle_center)
        worksheet.write(row, 6, 'list_price',format_minititle_center)
        worksheet.write(row, 7, 'standard_price',format_minititle_center)
        worksheet.write(row, 8, 'sale_delay',format_minititle_center)
        worksheet.write(row, 9, 'qty_multiply',format_minititle_center)

        worksheet.write(row, 10, 'variant_seller_ids/name',format_minititle_center)
        worksheet.write(row, 11, 'variant_seller_ids/product_id',format_minititle_center)
        worksheet.write(row, 12, 'variant_seller_ids/price',format_minititle_center)
        worksheet.write(row, 13, 'variant_seller_ids/min_qty',format_minititle_center)
        worksheet.write(row, 14, 'moq_ids/product_variant_id',format_minititle_center)
        worksheet.write(row, 15, 'moq_ids/min_qty',format_minititle_center)
        worksheet.write(row, 16, 'moq_ids/price_unit',format_minititle_center)

        row+=1
        row_p = row
        for product in products:

            external_id = product.get_external_id().get(product.id)
            if not external_id:
                request.env['ir.model.data'].sudo().create({
                    'name':     data_obj1+'_'+str(product.id),
                    'module': "__export__",
                    'res_id': product.id,
                    'model': data_obj,
                    'noupdate': True
                })

            worksheet.write(row_p, 0, product.get_external_id().get(product.id),format_minititle_center)
            worksheet.write(row_p, 3, product.default_code or '',format_minititle_center)
            worksheet.write(row_p, 4, product.name,format_minititle_center)
            worksheet.write(row_p, 5, product.product_brand_id.name or '',format_minititle_center)
            worksheet.write(row_p, 6, product.list_price,format_minititle_center)
            worksheet.write(row_p, 7, product.standard_price,format_minititle_center)
            worksheet.write(row_p, 8, product.sale_delay or '',format_minititle_center)
            worksheet.write(row_p, 9, product.qty_multiply or '',format_minititle_center)

            row_l1 = row_p - 1
            row_l2 = row_p -1
            data_variant_seller = product.variant_seller_ids
            if data_obj == 'product.product':
                data_variant_seller = data_variant_seller.filtered(lambda line: line.product_id==product)
            if data_variant_seller:
                for variant_seller in data_variant_seller.sorted(key=lambda line: (line.product_id.id)):
                    row_l1+=1

                    external_id = variant_seller.get_external_id().get(variant_seller.id)
                    if not external_id:
                        request.env['ir.model.data'].sudo().create({
                            'name':     'product_supplierinfo_'+str(variant_seller.id),
                            'module': '__export__',
                            'res_id': variant_seller.id,
                            'model': 'product.supplierinfo',
                            'noupdate': True
                        })

                    worksheet.write(row_l1, 1, variant_seller.get_external_id().get(variant_seller.id),format_minititle_center)
                    worksheet.write(row_l1, 10, variant_seller.name.display_name or '',format_minititle_center)
                    worksheet.write(row_l1, 11, variant_seller.product_id.display_name or '',format_minititle_center)
                    worksheet.write(row_l1, 12, variant_seller.price,format_minititle_center)
                    worksheet.write(row_l1, 13, variant_seller.min_qty,format_minititle_center)
            
            data_moq = product.moq_ids
            if data_obj == 'product.product':
                data_moq = data_moq.filtered(lambda line: line.product_variant_id==product)
            if data_moq: 
                for moq in data_moq.sorted(key=lambda line: (line.product_variant_id.id)):
                    row_l2+=1

                    external_id = moq.get_external_id().get(moq.id)
                    if not external_id:
                        request.env['ir.model.data'].sudo().create({
                            'name':     'mccoy_product_moq_'+str(moq.id),
                            'module': '__export__',
                            'res_id': moq.id,
                            'model': 'mccoy.product.moq',
                            'noupdate': True
                        })

                    worksheet.write(row_l2, 2, moq.get_external_id().get(moq.id),format_minititle_center)
                    worksheet.write(row_l2, 14, moq.product_variant_id.display_name or '',format_minititle_center)
                    worksheet.write(row_l2, 15, moq.min_qty or '',format_minititle_center)
                    worksheet.write(row_l2, 16, moq.price_unit,format_minititle_center)
                

            if row_l1 > row_p:
                row_p=row_l1+1
            elif row_l2 > row_p:
                row_p=row_l2+1
            else:
                row_p+=1

        

        workbook.close()
        xlsx_data = output.getvalue()
        response = request.make_response(
            xlsx_data,
            headers=[('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                    ('Content-Disposition', 'attachment; filename=%s (Export).xlsx' % data_obj)]
        )
        return response



class ProductConfiguratorController(ProductConfiguratorController):

    @http.route(['/sale_product_configurator/configure'], type='json', auth="user", methods=['POST'])
    def configure(self, product_template_id, pricelist_id,partnerId, **kw):
        add_qty = int(kw.get('add_qty', 1))
        company = request.env.user.company_id
        product_template = request.env['product.template'].browse(int(product_template_id))
        pricelist = self._get_pricelist(pricelist_id)
        currency_id = company.currency_id.id
        product_combination = False
        attribute_value_ids = set(kw.get('product_template_attribute_value_ids', []))
        attribute_value_ids |= set(kw.get('product_no_variant_attribute_value_ids', []))
        if attribute_value_ids:
            product_combination = request.env['product.template.attribute.value'].browse(attribute_value_ids)

        if pricelist:
            product_template = product_template.with_context(pricelist=pricelist.id, partner=request.env.user.partner_id)
            currency_id = pricelist.currency_id.id
        return request.env['ir.ui.view']._render_template("sale_product_configurator.configure", {
            'product': product_template,
            'pricelist': pricelist,
            'qty_multiply':product_template.qty_multiply or 1,
            'add_qty': add_qty,
            'havemoq':product_template.moq_ids.ids or '',
            'currency_id':currency_id,
            'product_combination': product_combination,
            'cust_id':partnerId
        })
