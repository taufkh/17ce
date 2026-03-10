from odoo import api, fields, models, tools, _
from dateutil.relativedelta import relativedelta

class OdesRequestPurchaseOrderWizard(models.TransientModel):
    _name = "odes.request.purchase.order.wizard"
    _description = "Odes Request Purchase Order Wizard"

    name = fields.Char(string="Name")
    date_start = fields.Date('Starting Date', default=fields.Date.today())
    line_ids = fields.One2many('odes.request.purchase.order.wizard.line', 'request_id', string="Lines")



    @api.model
    def default_get(self, fields):
        res = super(OdesRequestPurchaseOrderWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        picking_obj = self.env['stock.picking']
        list_name = ""
        list_data = []
        no = 1
        for delivery in picking_obj.browse(active_ids):
            if no != len(active_ids):
                list_name += delivery.origin + ","
            else:
                list_name += delivery.origin
            no += 1

            dict_data_po = {}
            total_qty_sum = 0
            # list_data_po = []
            for line in delivery.move_ids_without_package:
                if not line.purchase_id:
                    if line.product_id.id not in dict_data_po:
                        
                        data_po = {'product_qty': line.product_uom_qty}
                        dict_data_po[line.product_id.id] = data_po
                    else:
                        total_qty_sum = dict_data_po[line.product_id.id]['product_qty'] + line.product_uom_qty
                        dict_data_po[line.product_id.id]['product_qty'] = total_qty_sum
            # print (dict_data_po, 'ffg')

            for line in dict_data_po:
                # print (line, 'dffg')
                qty_demand = dict_data_po[line]['product_qty']
                product = self.env['product.product'].browse(line)
                minimum_stock = 0
                if product.orderpoint_ids:
                    for orderpoint in product.orderpoint_ids:
                        minimum_stock = orderpoint.product_min_qty

                list_data.append([0, 0, {
                    'product_id': line,
                    'partner_id': product.product_tmpl_id.manufacturing_company_id.id or False,
                    'qty': qty_demand + minimum_stock,
                    'qty_demand': qty_demand,
                    # 'move_id' : line.id
                     
                }])
            
        res['line_ids'] = list_data
        res['name'] = list_name
        
        return res

    def action_create_po(self):
        active_ids = self.env.context.get('active_ids', [])
        for rec in self:
            
            dict_data_po = {}
            
            ### Rework line grouping for PO, old algo weirdly mix up and duplicate if the same partner is
            #another partner in between



            # list_data_po = []
            for line in rec.line_ids.sorted(lambda p: p.partner_id):
                if line.partner_id.id not in dict_data_po:
                    dict_data_po[line.partner_id.id] = {'lines': []}
                    dict_data_po[line.partner_id.id]['lines'].append(line)
                    # list_data_po = []
                    # list_data_po.append(line)
                    # data_po = {'lines': list_data_po}
                    
                    # dict_data_po[line.partner_id.id] = data_po
                    # print (data_po, " === data_po") 
                else:
                    # list_data_po.append(line)
                    # dict_data_po[line.partner_id.id]['lines'] = list_data_po
                    dict_data_po[line.partner_id.id]['lines'].append(line)
                    # print (list_data_po, "==== data PO")
            purchase_data_list = []
            for data in dict_data_po:
                po_vals = rec.sudo()._prepare_auto_purchase_order_data(data)
                item_list_ids = []
                list_order_line = []
                for line_data in dict_data_po[data]['lines']:
                    if line_data.qty > 0:
                        # po_vals['order_line'] += [(0, 0, rec._prepare_auto_purchase_order_line_data(line_data))]
                        item_list_ids.append(line_data.product_id.id)
                        list_order_line.append((0, 0, rec._prepare_auto_purchase_order_line_data(line_data)))
                po_vals['order_line'] = list_order_line                
                
                purchase_order = self.env['purchase.order'].create(po_vals)
                move_ids = self.env['stock.move'].search([('picking_id','in', active_ids),('product_id','in', item_list_ids)])
                if move_ids:
                    move_ids.write({'purchase_id' : purchase_order.id})
                purchase_data_list.append(purchase_order.id)
            action = self.env.ref('purchase.purchase_form_action').read()[0]
            
            action['domain'] = [('id', '=', purchase_data_list)]
            return action
                # for line in rec.line_ids:
                #     if line.qty > 0:
                #         line.move_id.write({'purchase_id' : purchase_order.id})
            # gg


    def _prepare_auto_purchase_order_data(self,partner_id):
        
        self.ensure_one()
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'),('company_id', '=', self.env.company[0].id)],limit=1)
        
        return {
            'name': self.env['ir.sequence'].sudo().next_by_code('purchase.order'),
            'origin': self.name,
            'partner_id': partner_id,
            'picking_type_id': picking_type.id,
            'date_order': fields.datetime.now(),
            # 'company_id': company.id,
            # 'fiscal_position_id': company_partner.property_account_position_id.id,
            # 'payment_term_id': company_partner.property_supplier_payment_term_id.id,
            # 'auto_generated': True,
            # 'auto_sale_order_id': self.id,
            # 'partner_ref': self.name,
            'currency_id': self.env.user.company_id.currency_id.id,
            'order_line': [],
        }

    @api.model
    def _prepare_auto_purchase_order_line_data(self, line):
        
        return {
            'name': line.product_id.name,
            'product_qty': line.qty,
            'product_id': line.product_id and line.product_id.id or False,
            'product_uom': line.product_id and line.product_id.uom_po_id.id or line.product_uom.id,
            'price_unit': line.product_id.standard_price,
            # 'company_id': company.id,
            # 'date_planned': so_line.order_id.expected_date or date_order,
            # 'taxes_id': [(6, 0, company_taxes.ids)],
            # 'display_type': so_line.display_type,
        }

class OdesRequestPurchaseOrderWizardLine(models.TransientModel):
    _name = "odes.request.purchase.order.wizard.line"
    _description = "Odes Request Purchase Order Wizard Line"

    request_id = fields.Many2one('odes.request.purchase.order.wizard', string="Request id")
    product_id = fields.Many2one('product.product', string="Product")
    move_id = fields.Many2one('stock.move', string="Move")
    partner_id = fields.Many2one('res.partner', string='Vendor', help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    
    qty = fields.Float(string="Quantity")
    qty_demand = fields.Float(string="Quantity Demand")
    
    is_create_po = fields.Boolean(string="Create PO")


