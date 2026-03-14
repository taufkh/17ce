# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import html2plaintext
import math
from datetime import timedelta

class SaleOrder(models.Model):
    _inherit = "sale.order"
    _order = "old_name desc, revision desc"


    def _get_order_line(self):
        for order in self:
            order.order_line_related = order.order_line

    def _inverse_order_line(self):
        for order in self:
            order.order_line = order.order_line_related

    quotation_type = fields.Selection([('item', 'Item'), ('service', 'Service')], readonly=True, string='Type', default='item', copy=True)
    breakdown_line_ids = fields.One2many('sale.order.breakdown.line', 'order_id', string='Breakdown Phase', copy=True)
    timeline_remark = fields.Text('Timeline Remark', copy=True, default=lambda self: self.env.company.quotation_timeline_remark)
    timeline_line_ids = fields.One2many('sale.order.timeline.line', 'order_id', string='Proposed Project Timeline', copy=True)
    order_line_related = fields.One2many('sale.order.line', compute='_get_order_line', inverse='_inverse_order_line')
    service_description = fields.Char('Description', copy=True, default=lambda self: self.env.company.quotation_description)
    service_contact_person = fields.Char('Contact Person')
    service_contact_person_title = fields.Char('Contact Person\'s Title')
    service_contact_person_phone = fields.Char('Contact Person\'s Phone')
    service_contact_person_email = fields.Char('Contact Person\'s Email')
    service_contact_person_office_tel = fields.Char('Contact Person\'s Office Tel')
    is_confirmed = fields.Boolean('Confirmed', copy=False)
    quotation_date = fields.Datetime('Quotation Date', copy=False, default=fields.Datetime.now)
    
    old_name = fields.Char("Old Name", compute="_get_old_name", store=True) 
    revision = fields.Integer('Revision', default=0, copy=False)
    is_current = fields.Boolean('Current Revision', default=True, copy=False)
    quotation_sale_id = fields.Many2one('sale.order', 'Quotation', copy=False)
    is_dont_multiple = fields.Boolean("Don't Multiple")
    is_wst = fields.Boolean('WST', default=False, store=True, compute='_get_wst')

    @api.depends('sale_order_template_id')
    def _get_wst(self):
        for order in self:
            wst = False
            if order.sale_order_template_id.is_wst:
                wst = True
            order.is_wst = wst
            
    @api.depends("name", "revision")
    def _get_old_name(self):
        for order in self:
            order.old_name = order.name.split("-R")[0]

    @api.onchange('quotation_type')
    def _onchange_quotation_type(self):
        for order in self:
            order.order_line = False
            order.order_line_related = False

    @api.onchange('sale_order_template_id')
    def onchange_sale_order_template_id(self):
        if not self.sale_order_template_id:
            self.require_signature = self._get_default_require_signature()
            self.require_payment = self._get_default_require_payment()
            return

        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)

        # --- first, process the list of products from the template
        order_lines = [(5, 0, 0)]
        for line in template.sale_order_template_line_ids:
            data = self._compute_line_data_for_template_change(line)

            if line.product_id:
                price = line.price_unit
                discount = 0

                if self.pricelist_id:
                    pricelist_price = self.pricelist_id.with_context(uom=line.product_uom_id.id).get_product_price(line.product_id, 1, False)

                    if self.pricelist_id.discount_policy == 'without_discount' and price:
                        discount = max(0, (price - pricelist_price) * 100 / price)
                    else:
                        price = pricelist_price

                data.update({
                    'price_unit': price,
                    'original_price': line.original_price,
                    'discount': discount,
                    'product_uom_qty': line.product_uom_qty,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'price_unit': line.price_unit,
                    'customer_lead': self._get_customer_lead(line.product_id.product_tmpl_id),
                    'service_line_type': line.service_line_type,
                })
                if self.quotation_type == 'service':
                    data.update({
                        'team_members': line.team_members,
                        'deliverables': line.deliverables,
                    })

            order_lines.append((0, 0, data))

        if self.quotation_type == 'item':
            self.order_line = order_lines
            self.order_line._compute_tax_id()

        if self.quotation_type == 'service':
            self.order_line_related = order_lines
            self.order_line_related._compute_tax_id()

            breakdown_lines = [(5, 0, 0)]
            for line in template.breakdown_line_ids:
                breakdown_data = {
                    'sequence': line.sequence,
                    'name': line.name,
                }
                
                breakdown_phase_lines = [(5, 0, 0)]
                for phase_line in line.breakdown_phase_line_ids:
                    phase_data = {
                        'sequence': phase_line.sequence,
                        'name': phase_line.name,
                        'stages': phase_line.stages,
                        'consultation': phase_line.consultation,
                        'days': phase_line.days,
                    }
                    breakdown_phase_lines.append((0, 0, phase_data))
                breakdown_data.update({
                    'breakdown_phase_line_ids': breakdown_phase_lines,
                })

                breakdown_lines.append((0, 0, breakdown_data))

            self.breakdown_line_ids = breakdown_lines

            timeline_lines = [(5, 0, 0)]
            for line in template.timeline_line_ids:
                timeline_data = {
                    'sequence': line.sequence,
                    'name': line.name,
                    'start_date': line.start_date,
                    'end_date': line.end_date,
                }
                
                timeline_lines.append((0, 0, timeline_data))

            self.timeline_line_ids = timeline_lines

        # then, process the list of optional products from the template
        option_lines = [(5, 0, 0)]
        for option in template.sale_order_template_option_ids:
            data = self._compute_option_data_for_template_change(option)
            option_lines.append((0, 0, data))

        self.sale_order_option_ids = option_lines

        if template.number_of_days > 0:
            self.validity_date = fields.Date.context_today(self) + timedelta(template.number_of_days)

        self.require_signature = template.require_signature
        self.require_payment = template.require_payment

        if template.note:
            self.note = template.note

        self.service_description = template.service_description
        self.service_contact_person = template.service_contact_person
        self.service_contact_person_title = template.service_contact_person_title
        self.service_contact_person_phone = template.service_contact_person_phone
        self.service_contact_person_email = template.service_contact_person_email
        self.service_contact_person_office_tel = template.service_contact_person_office_tel
        self.timeline_remark = template.timeline_remark

    def button_readjust_taxes(self):
        tax_obj = self.env['account.tax']
        for line in self.order_line_related + self.order_line:
            taxes = []
            for tax in line.tax_id:
                if tax.company_id != self.company_id:                    
                    tax_record = tax_obj.search([('name', '=', tax.name), ('amount', '=', tax.amount), ('company_id', '=', self.company_id.id)], limit=1)
                    if tax_record:
                        taxes.append(tax_record.id)
                    else:                        
                        raise ValidationError( ("Tax %s can't be found on %s company, please set the equivalent tax !") % (tax.name, self.company_id.name) )
            if taxes:
                line.write({'tax_id': [(6, 0, taxes)]})

    def action_confirm(self):
        context = dict(self.env.context or {})
        if len(self) == 1:
            if self.is_dont_multiple:
                return super(SaleOrder, self).action_confirm()
        if context.get('use_default'):
            return super(SaleOrder, self).action_confirm()
        elif self.company_id.quotation_to_company_id and self.company_id.quotation_old_prefix and self.company_id.quotation_new_prefix and not self.is_confirmed:
            name = self.name
            company_id = self.company_id.quotation_to_company_id.id
            warehouse_id = self.sudo().user_id.with_company(company_id)._get_default_warehouse_id().id
            sequence_id = self.company_id.quotation_prefix_id
            if self.partner_id.company_id and self.partner_id.company_id.id != company_id:
                self.partner_id.write({'company_id' : False})
                # raise UserError(_('Please select customer with no company'))

            default = {}
            if sequence_id:
                # if '/' in name:
                #     replace_index = name.rindex('/')
                #     name = name.replace(name[0:replace_index+1], self.company_id.quotation_new_prefix)
                name = name.replace(self.company_id.quotation_old_prefix, self.company_id.quotation_new_prefix)
                default['name'] = name
            default['company_id'] = company_id
            default['warehouse_id'] = warehouse_id
            default['opportunity_id'] = self.opportunity_id.id or False
            if self.company_id != self.company_id.quotation_to_company_id:
                default['opportunity_id'] = False
            default['quotation_sale_id'] = self.id
            default['quotation_date'] = self.quotation_date
            default['is_confirmed'] = True
            default['revision'] = self.revision
            sale_order = self.sudo().with_context({'keep_name': 1}).copy(default=default)

            sale_order.sudo().with_context({'use_default': 1}).action_confirm()
            for line in sale_order.sudo().order_line:
                name = line.sudo().name
                price_unit = line.sudo().price_unit
                
                # line.sudo().product_id_change()
                
                line.sudo().name = name
                line.sudo().price_unit = price_unit


            sale_order.button_readjust_taxes()

            self.is_confirmed = True
            self.state = 'done'
        else:
            return super(SaleOrder, self).action_confirm()

    @api.model_create_multi
    def create(self, vals_list):
        context = dict(self.env.context or {})
        company_obj = self.env['res.company']
        sequence_obj = self.env['ir.sequence']

        for vals in vals_list:
            company_id = vals.get('company_id', False)
            company = company_obj.browse(company_id)
            if company.quotation_prefix_id:
                seq_date = None
                if 'date_order' in vals:
                    seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))

                ###Quotation Revision Control
                ###Quotation Copy Number
                if not context.get('keep_name'):
                    vals['name'] = sequence_obj.next_by_code(company.quotation_prefix_id.code, sequence_date=seq_date) or _('New')
        result = super(SaleOrder, self.with_context(dont_create_revision=True)).create(vals_list)

        return result

    def write(self, vals):
        field_list = ['price_unit', 'product_uom_qty']
        update_revision = False

        if 'order_line' in vals:
            for line in vals['order_line']:
                if type(line) is list and len(line) >= 3:
                    if line[0] == 0:
                        update_revision = True
                        break
                    elif line[0] == 1 and type(line[2]) is dict:
                        line_vals = line[2]
                        for f in field_list:
                            if f in line_vals:
                                update_revision = True
                                break
                    elif line[0] == 2:
                        update_revision = True
                        break
                if update_revision:
                    break

        elif 'order_line_related' in vals:
            for line in vals['order_line_related']:
                if type(line) is list and len(line) >= 3:
                    if line[0] == 0:
                        update_revision = True
                        break
                    elif line[0] == 1 and type(line[2]) is dict:
                        line_vals = line[2]
                        for f in field_list:
                            if f in line_vals:
                                update_revision = True
                                break
                    elif line[0] == 2:
                        update_revision = True
                        break
                if update_revision:
                    break

        if update_revision:
            self.new_revision()

        return super(SaleOrder, self).write(vals)

    def new_revision(self):
        context = dict(self.env.context or {})
        for sale in self:
            name = sale.name.split('-R')
            old_name = name[0]
            if len(sale.name.split('-R')) == 1:
                #sale.revision = 2
                new_sale = sale.with_context({'keep_name': 1}).copy(default={'name': old_name, 'state': 'done', 'is_confirmed': True, 'is_current': False, 'quotation_date': sale.quotation_date, 'date_order': sale.quotation_date, 'revision': sale.revision})
            else:
                new_sale = sale.with_context({'keep_name': 1}).copy(default={'name': old_name+'-R'+str(sale.revision), 'state': 'done', 'is_confirmed': True, 'is_current': False, 'quotation_date': sale.quotation_date, 'date_order': sale.quotation_date, 'revision': sale.revision})
            sale.revision = sale.revision + 1
            sale.name = old_name+'-R'+str(sale.revision)
        return True

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        sale_order = super(SaleOrder, self).copy(default)
        return sale_order

    def action_unlock_draft(self):
        self.write({'state': 'draft'})

    def action_lock(self):
        self.write({'state': 'done'})

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _default_service_product_id(self):
        quotation_type = self.env.context.get('quotation_type', False)
        if quotation_type:
            if quotation_type == 'service':
                if self.env.company.quotation_default_product_id:
                    return self.env.company.quotation_default_product_id.id
                else:
                    raise UserError(_('Please set default product in Configuration'))
        return False

    team_members = fields.Text('Team Members')
    deliverables = fields.Text('Deliverables')
    product_id = fields.Many2one('product.product', default=_default_service_product_id)
    service_line_type = fields.Selection([
        ('day', 'Day'),
        ('off', 'Off'),
        ], string='Type', default='day')
    original_price = fields.Float('Original Price', digits='Product Price', default=0.0)

    def get_sale_order_line_multiline_description_sale(self, product):
        quotation_type = self.env.context.get('quotation_type', False)
        if quotation_type == 'service':
            return ""
        else:
            return super(SaleOrderLine, self).get_sale_order_line_multiline_description_sale(product)

    @api.onchange('service_line_type')
    def _onchange_service_line_type(self):
        if self.service_line_type == 'off':
            self.product_uom_qty = 1

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        if self.order_id.quotation_type == 'service':
            res.update({'name': html2plaintext(self.name)})
        return res

    def get_total_original_price(self):
        price = self.original_price
        if price:
            taxes = self.tax_id.compute_all(price, self.order_id.currency_id, self.product_uom_qty, product=self.product_id, partner=self.order_id.partner_shipping_id)
            return taxes['total_excluded']
        else:
            return 0

class SaleOrderBreakdownLine(models.Model):
    _name = 'sale.order.breakdown.line'
    _description = 'Sales Order Breakdown Line'
    _order = 'order_id, sequence, id'

    name = fields.Char('Name')
    sequence = fields.Integer(string='Sequence', default=10)
    order_id = fields.Many2one('sale.order', string='Order Reference', ondelete='cascade')
    breakdown_phase_line_ids = fields.One2many('sale.order.breakdown.phase.line', 'breakdown_id', string='Breakdown Phase', copy=True)

class SaleOrderBreakdownPhaseLine(models.Model):
    _name = 'sale.order.breakdown.phase.line'
    _description = 'Sales Order Breakdown Phase Line'
    _order = 'breakdown_id, sequence, id'

    def _get_total_mandays(self):
        for line in self:
            line.total_mandays = line.consultation * line.days

    name = fields.Text('Activities')
    sequence = fields.Integer(string='Sequence', default=10)
    breakdown_id = fields.Many2one('sale.order.breakdown.line', string='Breakdown Phase', ondelete='cascade')
    stages = fields.Text('Stages')
    consultation = fields.Float('Consult.')
    days = fields.Float('No. of Days')
    total_mandays = fields.Float('Total Man-days', compute='_get_total_mandays')

class SaleOrderTimelineLine(models.Model):
    _name = 'sale.order.timeline.line'
    _description = 'Sales Order Timeline Line'
    _order = 'order_id, sequence, id'

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
    order_id = fields.Many2one('sale.order', string='Order Reference', ondelete='cascade')
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
