# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression  


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # def _get_domain_purchase_order_line_id(self):
    #     cr = self.env.cr
    #     domain = []
    #     context = self.env.context
    #     product_id = self.product_id
    #     if product_id:
    #         query = """
    #             SELECT id 
    #             FROM purchase_order_line 
    #             WHERE 
    #             id NOT IN (
    #                 SELECT purchase_order_line_id FROM sale_order_line 
    #                 WHERE purchase_order_line_id IS NOT NULL
    #                     AND product_id = {product_id}
    #                 )
    #             AND product_id = {product_id}
    #             AND state IN ('purchase','done')
    #           """.format(product_id=product_id.id)
    #         cr.execute(query) 
    #         line_ids  = [x for x in  map(lambda x: x[0], cr.fetchall())]
    #         domain = [('id','in',line_ids)] 
    #     return domain

    #PO to Supplier
    purchase_order_line_id = fields.Many2one('purchase.order.line', string="Purchase Order Line")


    def action_link_po_to_supplier(self):
        cr = self.env.cr
        # context = self._context
        context = {}

        product_id = self.product_id
        # query = """
        #     SELECT pol.id, po.name
        #     FROM purchase_order_line  AS pol
        #     INNER JOIN purchase_order AS po ON po.id = pol.order_id
        #     WHERE 
        #         pol.id NOT IN (
        #             SELECT purchase_order_line_id FROM sale_order_line 
        #             WHERE purchase_order_line_id IS NOT NULL
        #                 AND product_id = {product_id}
        #                 AND company_id = {company_id}
        #             )
        #         AND pol.product_id = {product_id}
        #         AND pol.state IN ('purchase','done')
        #         AND pol.company_id = {company_id}
        #   """.format(product_id=product_id.id, company_id=self.company_id.id)

        query = """
            SELECT pol.id, po.name, pol.price_unit
            FROM purchase_order_line  AS pol
            INNER JOIN purchase_order AS po ON po.id = pol.order_id
            WHERE pol.product_id = {product_id}
                --pol.state IN ('purchase','done')
                AND pol.company_id = {company_id}
          """.format(product_id=product_id.id, company_id=self.company_id.id)
        # print("query:::",query)
        cr.execute(query) 
        results = cr.fetchall()
        line_ids = []
        for result in results:
            line_ids  += [(0,0,{
                    'purchase_order_line_id':result[0],
                    'purchase_number':result[1],
                    'purchase_price_unit':result[2],
                })]
        context['default_line_ids'] = line_ids
        context['default_sale_order_line_id'] = self.id
        action =  {
            'name': _('Link S.O. to P.O'),
            'res_model': 'odes.sale.link.po.to.supplier',
            'view_mode': 'form',
            'view_id': self.env.ref('odes_sale_reporting.odes_sale_link_po_to_supplier_views_wizard_form').sudo().id,
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window', 
        }
        return action