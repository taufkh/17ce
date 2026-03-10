# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import html2plaintext
import math
from datetime import timedelta

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _get_user_from_config(self, ref_key, id_key):
        param_env = self.env['ir.config_parameter'].sudo()
        user = False
        user_ref = (param_env.get_param(ref_key) or '').strip()
        user_id = (param_env.get_param(id_key) or '').strip()
        if user_ref:
            user = self.env.ref(user_ref, raise_if_not_found=False)
        elif user_id.isdigit():
            user = self.env['res.users'].browse(int(user_id))
        return user if user and user.exists() else self.env['res.users']

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

    def _compute_users(self):
        confirm_user = self._get_user_from_config('odes_sign.purchase_confirm_user_ref', 'odes_sign.purchase_confirm_user_id')
        for order in self:
            order.user_confirm_id = confirm_user.id if confirm_user else False

    def _compute_users_approve(self):
        approve_user = self._get_user_from_config('odes_sign.purchase_approve_user_ref', 'odes_sign.purchase_approve_user_id')
        for order in self:
            order.user_approve_id = approve_user.id if approve_user else False



    user_confirm_id = fields.Many2one('res.users',compute="_compute_users", string='User Confirm', copy=False)
    user_approve_id = fields.Many2one('res.users',compute="_compute_users_approve", string='User Approved', copy=False)
    is_submit = fields.Boolean(string='Submit', copy=False)
    move_count = fields.Integer("Sale Order", compute='_compute_sale_count')


    def _compute_sale_count(self):

        for purchase in self:
            list_sale = []
            move_obj = self.env['stock.move'].search([('purchase_id', '=', purchase.id)])
            for move in move_obj:
                if move.sale_line_id and move.sale_line_id.order_id.id in list_sale:
                    continue
                else:
                    list_sale.append(move.sale_line_id.order_id.id)
            if list_sale and list_sale[0] == False:
                list_sale = []
            purchase.move_count = len(list_sale)


    def action_view_sale(self):
        '''
        This function returns an action that displays the opportunities from partner.
        '''
        list_sale = []
        for purchase in self:
            list_sale = []
            move_obj = self.env['stock.move'].search([('purchase_id', '=', purchase.id)])
            for move in move_obj:
                if move.sale_line_id and move.sale_line_id.order_id.id in list_sale:
                    continue
                else:
                    list_sale.append(move.sale_line_id.order_id.id)
            action = self.env.ref('sale.action_orders').read()[0]
            
            action['domain'] = [('id', '=', list_sale)]
            return action
    

    def action_submit(self):
        context = dict(self.env.context or {})
        for order in self:
            if not order.is_submit:
                self._create_activity()
                order.write({'is_submit' : True})
            else:
                raise UserError(_("Order %s already submit !")% (order.name))



    def _create_activity(self):
        confirm_user = self._get_user_from_config('odes_sign.purchase_confirm_user_ref', 'odes_sign.purchase_confirm_user_id')
        activity_type = self.env.ref('odes_sign.mail_activity_data_odes_sign_purchase', raise_if_not_found=False)
        if not activity_type:
            return
        for purchase in self:
            group_purchase_confirm = self.env.ref('odes_sign.group_odes_purchase_confirm').users.ids
            target_user = confirm_user.id if confirm_user and confirm_user.id in group_purchase_confirm else (group_purchase_confirm[0] if group_purchase_confirm else False)
            if target_user:
                purchase.activity_schedule(activity_type.id, user_id=target_user)


    def action_create_invoice(self):
        res = super(PurchaseOrder, self).action_create_invoice()
        #for purchase in self:
        #    for invoice in self.invoice_ids:
        #        invoice.activity_schedule(
        #                'odes_sign.mail_activity_data_odes_sign_purchase_create_invoice',
        #                user_id=14)  
        return res

    def button_confirm(self):
        approve_user = self._get_user_from_config('odes_sign.purchase_approve_user_ref', 'odes_sign.purchase_approve_user_id')
        activity_type = self.env.ref('odes_sign.mail_activity_data_odes_sign_purchase_approved', raise_if_not_found=False)
        res = super(PurchaseOrder, self).button_confirm()
        for purchase in self:
            if purchase.state == 'to approve' and activity_type:
                purchase.activity_schedule(activity_type.id, user_id=(approve_user.id if approve_user else purchase.user_id.id))
        return res

        
        # self._create_activity()

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

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

    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        name = super(PurchaseOrderLine, self)._get_product_purchase_description(product_lang)
        context_data = self.env.context
        short_name_companies = self._get_companies_from_config('odes_sign.purchase_short_name_company_refs')
        should_use_short_name = (
            self.env.company in short_name_companies
            if short_name_companies else self.env.company == self.company_id
        )
        if should_use_short_name:
            if 'params' in context_data and 'model' in context_data['params'] and context_data['params']['model'] == 'purchase.order':
                name = product_lang.name
        
        # name = product_lang.display_name
        # if product_lang.description_purchase:
        #     name += '\n' + product_lang.description_purchase

        return name
