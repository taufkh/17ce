from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    term_condition = fields.Char('Term and Condition')
    is_smart_iot = fields.Boolean('Is Smart IOT')
    designation = fields.Char('Designation')
    select_address2 = fields.Selection(selection=[('address_1', 'Address 1'), ('address_2', 'Address 2'), ('address_3', 'Address 3')], string='Select Address 2')

    def get_term_condition (self):
        term_condition_obj = self.env['smart.iot.term.condition'].search([],limit=1)

        term_condition = term_condition_obj.term_condition
        return term_condition

    def action_confirm(self):
        if self.sale_order_template_id.name == 'SMART IOT':
            self.order_line.mapped('product_id').write({'company_id': False})

        return super(SaleOrder, self).action_confirm()

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends('sequence', 'order_id')
    def _compute_serial_number(self):
        if self.order_id.sale_order_template_id.name == 'SMART IOT':
            for order_line in self:
                if order_line.serial_numbers == 0:
                    serial_no = 1
                    for line in order_line.mapped('order_id').order_line:
                        line.serial_numbers = serial_no
                        if line.display_type not in ['line_section','line_note']:
                            serial_no += 1
        else:
            for order_line in self:
                if order_line.serial_numbers == 0:
                    serial_no = 1
                    for line in order_line.mapped('order_id').order_line:
                        line.serial_numbers = serial_no
                        serial_no += 1
       
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        if self.order_id.sale_order_template_id.name == 'SMART IOT':
            self.name = self.product_id.mccoy_smart_iot_desc
        else:
            return res
    
    @api.onchange('sale_order_template_id')
    def _onchange_check_so_template(self):
        if self.sale_order_template_id != False:
            if self.sale_order_template_id.name == 'SMART IOT':
                self.is_smart_iot = True
            else:
                self.is_smart_iot = False
        else:
            self.is_smart_iot = False

class SaleOrderTemplate(models.Model):
    _inherit = "sale.order.template"
