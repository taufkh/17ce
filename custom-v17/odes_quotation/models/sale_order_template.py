# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class SaleOrderTemplate(models.Model):
    _inherit = "sale.order.template"

    def _get_sale_order_template_line_ids(self):
        for order in self:
            order.sale_order_template_line_ids_related = order.sale_order_template_line_ids

    def _inverse_sale_order_template_line_ids(self):
        for order in self:
            order.sale_order_template_line_ids = order.sale_order_template_line_ids_related

    quotation_type = fields.Selection([('item', 'Item'), ('service', 'Service')], string='Type', default='item', copy=True)
    breakdown_line_ids = fields.One2many('sale.order.template.breakdown.line', 'sale_order_template_id', string='Breakdown Phase', copy=True)
    timeline_remark = fields.Text('Timeline Remark', copy=True, default=lambda self: self.env.company.quotation_timeline_remark)
    timeline_line_ids = fields.One2many('sale.order.template.timeline.line', 'sale_order_template_id', string='Proposed Project Timeline', copy=True)
    sale_order_template_line_ids_related = fields.One2many('sale.order.template.line', compute='_get_sale_order_template_line_ids', inverse='_inverse_sale_order_template_line_ids')
    service_description = fields.Char('Description', copy=True, default=lambda self: self.env.company.quotation_description)
    service_contact_person = fields.Char('Contact Person')
    service_contact_person_title = fields.Char('Contact Person\'s Title')
    service_contact_person_phone = fields.Char('Contact Person\'s Phone')
    service_contact_person_email = fields.Char('Contact Person\'s Email')
    service_contact_person_office_tel = fields.Char('Contact Person\'s Office Tel')
    is_wst = fields.Boolean('WST', default=False)

    @api.onchange('quotation_type')
    def _onchange_quotation_type(self):
        for order in self:
            order.sale_order_template_line_ids = False
            order.sale_order_template_line_ids_related = False

class SaleOrderTemplateLine(models.Model):
    _inherit = "sale.order.template.line"

    def _default_service_product_id(self):
        quotation_type = self.env.context.get('quotation_type', False)
        if quotation_type:
            if quotation_type == 'service':
                if self.env.company.quotation_default_product_id:
                    return self.env.company.quotation_default_product_id.id
                else:
                    raise UserError(_('Please set default product in Configuration'))
        return False

    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    team_members = fields.Text('Team Members')
    deliverables = fields.Text('Deliverables')
    product_id = fields.Many2one('product.product', default=_default_service_product_id)
    service_line_type = fields.Selection([
        ('day', 'Day'),
        ('off', 'Off'),
        ], string='Type', default='day')
    original_price = fields.Float('Original Price', digits='Product Price', default=0.0)

    @api.onchange('service_line_type')
    def _onchange_service_line_type(self):
        if self.service_line_type == 'off':
            self.product_uom_qty = 1

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.ensure_one()
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id

            quotation_type = self.env.context.get('quotation_type', False)
            if quotation_type == 'service':
                self.name = ''
            else:
                self.name = self.product_id.get_product_multiline_description_sale()

class SaleOrderTemplateBreakdownLine(models.Model):
    _name = 'sale.order.template.breakdown.line'
    _description = 'Sales Order Template Breakdown Line'
    _order = 'sale_order_template_id, sequence, id'

    name = fields.Char('Name')
    sequence = fields.Integer(string='Sequence', default=10)
    sale_order_template_id = fields.Many2one('sale.order.template', string='Order Reference', ondelete='cascade')
    breakdown_phase_line_ids = fields.One2many('sale.order.template.breakdown.phase.line', 'breakdown_id', string='Breakdown Phase', copy=True)

class SaleOrderTemplateBreakdownPhaseLine(models.Model):
    _name = 'sale.order.template.breakdown.phase.line'
    _description = 'Sales Order Template Breakdown Phase Line'
    _order = 'breakdown_id, sequence, id'

    def _get_total_mandays(self):
        for line in self:
            line.total_mandays = line.consultation * line.days

    name = fields.Text('Activities')
    sequence = fields.Integer(string='Sequence', default=10)
    breakdown_id = fields.Many2one('sale.order.template.breakdown.line', string='Breakdown Phase', ondelete='cascade')
    stages = fields.Text('Stages')
    consultation = fields.Float('Consult.')
    days = fields.Float('No. of Days')
    total_mandays = fields.Float('Total Man-days', compute='_get_total_mandays')

class SaleOrderTemplateTimelineLine(models.Model):
    _name = 'sale.order.template.timeline.line'
    _description = 'Sales Order Template Timeline Line'
    _order = 'sale_order_template_id, sequence, id'

    def _get_duration(self):
        for line in self:
            weeks = math.ceil((line.end_date - line.start_date).days / 7)
            duration = ''

            if weeks > 1:
                duration = str(weeks) + ' weeks'
            else:
                duration = str(weeks) + ' week'

            line.duration =  duration

    name = fields.Text('Task / Descriptions')
    sequence = fields.Integer(string='Sequence', default=10)
    sale_order_template_id = fields.Many2one('sale.order.template', string='Order Reference', ondelete='cascade')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    duration = fields.Char('Duration', compute='_get_duration')

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            self.end_date = self.start_date

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            self.start_date = self.end_date