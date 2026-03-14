# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import html2plaintext
import math
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class SaleOrder(models.Model):
    _inherit = "sale.order"

    attach_oppurtunity_count = fields.Integer("Opportunity Attachment", compute='_compute_oppurtunity_count')
    signature = fields.Image(copy=True)
    signed_by = fields.Char(copy=True)
    signed_on = fields.Datetime(copy=True)

    def _get_companies_from_config(self, config_key):
        companies = self.env['res.company']
        raw_refs = (self.env['ir.config_parameter'].sudo().get_param(config_key) or '').strip()
        if not raw_refs:
            return companies
        for token in [x.strip() for x in raw_refs.split(',') if x.strip()]:
            if token.isdigit():
                companies |= self.env['res.company'].browse(int(token))
            else:
                company = self.env.ref(token, raise_if_not_found=False)
                if company and company._name == 'res.company':
                    companies |= company
        return companies.exists()

    def action_confirm(self):
        activity_companies = self._get_companies_from_config('odes_sign.confirm_activity_company_refs')
        if activity_companies:
            self.filtered(lambda order: order.company_id in activity_companies)._create_activity()
        return super(SaleOrder, self).action_confirm()

    def _create_activity(self):
        param_env = self.env['ir.config_parameter'].sudo()
        user = False
        user_ref = (param_env.get_param('odes_sign.confirm_activity_user_ref') or '').strip()
        user_id = (param_env.get_param('odes_sign.confirm_activity_user_id') or '').strip()
        if user_ref:
            user = self.env.ref(user_ref, raise_if_not_found=False)
        elif user_id.isdigit():
            user = self.env['res.users'].browse(int(user_id))
        activity_type = self.env.ref('odes_sign.mail_activity_data_odes_confirm_order', raise_if_not_found=False)
        if not activity_type:
            return
        for order in self:
            order.activity_schedule(activity_type.id, user_id=(user.id if user else order.user_id.id))
    
    def _compute_oppurtunity_count(self):

        for sale in self:
            acctach_opportunity = 0
            if sale.opportunity_id:
                acctach_opportunity = self.env['ir.attachment'].search_count(
                [('crm_lead_id', '=', sale.opportunity_id.id)])
            sale.attach_oppurtunity_count = acctach_opportunity


    def get_attachment(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Attachment',
            'view_mode': 'kanban,form',
            'res_model': 'ir.attachment',
            'domain': [('crm_lead_id', '=', self.opportunity_id.id)],
            'context': {'default_crm_lead_id':self.id, 'form_view_ref': 'odes_custom.odes_ir_attachment_view_form', 'kanban_view_ref':'odes_custom.odes_ir_attachment_kanban_form'}
        }

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_shipping_id': False,
            })
            return

        self = self.with_company(self.company_id)

        addr = self.partner_id.address_get(['delivery'])
        if self.partner_id.child_ids:
            for x in self.partner_id.child_ids:
                if x.type == 'delivery':
                    addr['delivery'] = x.id
        values = {
            'partner_shipping_id': addr['delivery'],
        }
        
        self.update(values)
        return res

    # def button_readjust_taxes(self):
    #     tax_obj = self.env['account.tax']
    #     for line in self.order_line_related:
    #         taxes = []
    #         for tax in line.tax_id:
    #             tax_record = tax_obj.search([('name', '=', tax.name), ('amount', '=', tax.amount), ('company_id', '=', self.company_id.id)], limit=1)
    #             if tax_record:
    #                 taxes.append(tax_record.id)
    #             else:
    #                 raise ValidationError( ("Tax %s can't be found on %s company, please set the equivalent tax !") % (tax.name, self.company_id.name) )
    #         if taxes:
    #             line.write({'tax_id': [(6, 0, taxes)]})

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    request_date = fields.Datetime('Request Date')
    promise_date = fields.Datetime('Promise Date')

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        price_unit = self.price_unit
        # print (price_unit, 'dfdfdf')
        res = super(SaleOrderLine, self).product_uom_change()
        # print (price_unit, 'price_unit')
        # print (self.price_unit, 'dd')
        if price_unit > 1:
            self.price_unit = price_unit
        return res

class SaleInvoiceForecast(models.Model):
    _inherit = 'sale.invoice.forecast'

    percent_amount = fields.Float(string='Percentage (%)')

    def sale_list_reminder(self):
        today = datetime.today()
        sales = self.env['sale.invoice.forecast'].search([])
        sale_list = []
        for rec in sales:
            check_date =  (rec.date_invoice+relativedelta(days =- 1))
            if today.date() == check_date:
                sale_list.append(rec)
        return sale_list

    def send_sale_invoice_forecast_reminder(self):
        if len(self.sale_list_reminder()) > 0:
            template_id = self.env.ref('odes_sign.odes_forecasted_invoiced_information_reminder').id
            template = self.env['mail.template'].browse(template_id)
            template.send_mail(self.id, force_send=True)

    def get_user_list(self):
        groups = self.env['res.groups'].search([('name','=','Billing')])
        return groups.users

    @api.onchange('percent_amount')
    def _onchange_percent_amount(self):
        if self.percent_amount:
            self.amount = (self.sale_id.amount_total * self.percent_amount)/100
