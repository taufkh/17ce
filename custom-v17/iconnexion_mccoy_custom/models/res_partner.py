
# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models, tools
from odoo.addons.bus.models.bus_presence import AWAY_TIMER
from odoo.addons.bus.models.bus_presence import DISCONNECTION_TIMER
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from datetime import timedelta

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'


    quotation_history_ids = fields.One2many('icon.quotation.history','partner_id', string="Quotation History")
    property_delivery_carrier_id = fields.Many2one('delivery.carrier', company_dependent=True, string="Delivery Method", help="Default delivery method used in sales orders.", default=lambda self: self.env.company.delivery_method_id)
    freight_terms_id = fields.Many2one('delivery.carrier', string='Freight Terms Method', default=lambda self: self.env.company.freight_term_id)
    purchase_delivery_method_id = fields.Many2one('delivery.carrier', string='Purchase Delivery Method')
    purchase_freight_terms_id = fields.Many2one('delivery.carrier', string='Purchase Freight Terms')

    #group field
    is_group_iconnexion_create_contact_under_company = fields.Boolean(string='Create Contact Under Company', compute='_compute_is_in_group')

    @api.constrains('user_id')
    def _onchange_salesperson_based_on_main_company(self):
        for partner in self:
            main_company = self.env['res.partner'].search([('parent_id', '=', partner.id)])
            for companies in main_company:
                companies.user_id = partner.user_id.id

    @api.model_create_multi
    def create(self, values_list):
        partners = super(Partner, self).create(values_list)
        for partner in partners:
            if partner.is_group_iconnexion_create_contact_under_company and not partner.parent_id:
                raise ValidationError("Cannot create a Company")
        return partners

    def _compute_is_in_group(self):
        for partner in self:
            if self.user_has_groups('iconnexion_mccoy_custom.group_iconnexion_create_contact_under_company'):
                partner.is_group_iconnexion_create_contact_under_company = True
            else:
                partner.is_group_iconnexion_create_contact_under_company = False

    @api.onchange('property_product_pricelist')
    def _onchange_pricelist_receivable_payable(self):
        for partner in self:
            if partner.property_product_pricelist and partner.property_product_pricelist.currency_id:
                currency_name = partner.property_product_pricelist.currency_id.name.lower()
                if currency_name == 'usd':
                    account_receivable = self.env['account.account'].search([('user_type_id.type', '=', 'receivable'), ('name', 'ilike', 'USD')], limit=1)
                    account_payable = self.env['account.account'].search([('user_type_id.type', '=', 'payable'), ('name', 'ilike', 'USD')], limit=1)
                elif currency_name == 'sgd':
                    account_receivable = self.env['account.account'].search([('user_type_id.type', '=', 'receivable'), ('name', 'ilike', 'SGD')], limit=1)
                    account_payable = self.env['account.account'].search([('user_type_id.type', '=', 'payable'), ('name', 'ilike', 'SGD')], limit=1)
                elif currency_name == 'eur':
                    account_receivable = self.env['account.account'].search([('user_type_id.type', '=', 'receivable'), ('name', 'ilike', 'EUR')], limit=1)
                    account_payable = self.env['account.account'].search([('user_type_id.type', '=', 'payable'), ('name', 'ilike', 'EUR')], limit=1)
                else:
                    return

                if account_receivable:
                    partner.property_account_receivable_id = account_receivable.id
                if account_payable:
                    partner.property_account_payable_id = account_payable.id

    def _compute_statements(self):
        if self:
            for rec in self:
                rec.sh_compute_boolean = False
                if rec.customer_rank > 0:
                    rec.sh_customer_statement_ids = False
                    rec.sh_customer_due_statement_ids = False
                    moves = self.env['account.move'].sudo().search([
                        ('partner_id', '=', rec.id),
                        ('move_type', 'in', ['out_invoice', 'out_refund']),
                        ('state', 'not in', ['draft', 'cancel']), ('is_proforma_invoice', '=', False)
                    ])
                    if moves:
                        move_paid = moves.filtered(
                            lambda x: x.amount_residual == 0)
                        rec.sh_customer_statement_ids.unlink()
                        statement_lines = []
                        for move in move_paid:
                            statement_vals = {
                                'sh_account':
                                rec.property_account_receivable_id.name,
                                'name': move.name,
                                'customer_ref': move.po_no,
                                'currency_id': move.currency_id.id,
                                'sh_customer_invoice_date': move.invoice_date,
                                'sh_customer_due_date': move.invoice_date_due,
                            }
                            if move.move_type == 'out_invoice':
                                statement_vals.update({
                                    'sh_customer_amount': move.amount_total,
                                    'sh_customer_paid_amount': move.amount_total - move.amount_residual,
                                    'sh_customer_balance': move.amount_total - (move.amount_total - move.amount_residual),
                                })
                            elif move.move_type == 'out_refund':
                                statement_vals.update({
                                    'sh_customer_amount': -(move.amount_total),
                                    'sh_customer_paid_amount': -(move.amount_total - move.amount_residual),
                                    'sh_customer_balance': -(move.amount_total - (move.amount_total - move.amount_residual)),
                                })
                            statement_lines.append((0, 0, statement_vals))
                        rec.sh_customer_statement_ids = statement_lines
                        rec.sh_customer_zero_to_thiry = 0.0
                        rec.sh_customer_thirty_to_sixty = 0.0
                        rec.sh_customer_sixty_to_ninety = 0.0
                        rec.sh_customer_ninety_plus = 0.0
                        today = fields.Date.today()
                        date_before_30 = today - timedelta(days=30)
                        date_before_60 = date_before_30 - timedelta(days=30)
                        date_before_90 = date_before_60 - timedelta(days=30)
                        moves_before_30_days = self.env['account.move'].sudo(
                        ).search([('move_type', 'in',
                                   ['out_invoice', 'out_refund']),
                                  ('partner_id', '=', rec.id),
                                  ('is_proforma_invoice', '=', False),
                                  ('invoice_date', '>=', date_before_30),
                                  ('invoice_date', '<=', fields.Date.today()),
                                  ('state', 'not in', ['draft', 'cancel'])])
                        moves_before_60_days = self.env['account.move'].sudo(
                        ).search([('move_type', 'in',
                                   ['out_invoice', 'out_refund']),
                                  ('partner_id', '=', rec.id),
                                  ('is_proforma_invoice', '=', False),
                                  ('invoice_date', '>=', date_before_60),
                                  ('invoice_date', '<=', date_before_30),
                                  ('state', 'not in', ['draft', 'cancel'])])
                        moves_before_90_days = self.env['account.move'].sudo(
                        ).search([('move_type', 'in',
                                   ['out_invoice', 'out_refund']),
                                  ('partner_id', '=', rec.id),
                                  ('is_proforma_invoice', '=', False),
                                  ('invoice_date', '>=', date_before_90),
                                  ('invoice_date', '<=', date_before_60),
                                  ('state', 'not in', ['draft', 'cancel'])])
                        moves_90_plus = self.env['account.move'].sudo().search(
                            [('move_type', 'in', ['out_invoice',
                                                  'out_refund']),
                             ('partner_id', '=', rec.id),
                             ('is_proforma_invoice', '=', False),
                             ('invoice_date', '<=', date_before_90),
                             ('state', 'not in', ['draft', 'cancel'])])
                        if moves_before_30_days:
                            total_paid = 0.0
                            total_amount = 0.0
                            total_balance = 0.0
                            for move_before_30 in moves_before_30_days:
                                if move_before_30.move_type == 'out_invoice':
                                    total_amount += move_before_30.amount_total
                                    total_paid += move_before_30.amount_total - move_before_30.amount_residual
                                elif move_before_30.move_type == 'out_refund':
                                    total_amount += -(move_before_30.amount_total)
                                    total_paid += -(move_before_30.amount_total - move_before_30.amount_residual)
                            total_balance = total_amount - total_paid
                            rec.sh_customer_zero_to_thiry = total_balance
                        if moves_before_60_days:
                            total_paid = 0.0
                            total_amount = 0.0
                            total_balance = 0.0
                            for move_before_60 in moves_before_60_days:
                                if move_before_60.move_type == 'out_invoice':
                                    total_amount += move_before_60.amount_total
                                    total_paid += move_before_60.amount_total - move_before_60.amount_residual
                                elif move_before_60.move_type == 'out_refund':
                                    total_amount += -(move_before_60.amount_total)
                                    total_paid += -(move_before_60.amount_total - move_before_60.amount_residual)
                            total_balance = total_amount - total_paid
                            total_balance = total_amount - total_paid
                            rec.sh_customer_thirty_to_sixty = total_balance
                        if moves_before_90_days:
                            total_paid = 0.0
                            total_amount = 0.0
                            total_balance = 0.0
                            for move_before_90 in moves_before_90_days:
                                if move_before_90.move_type == 'out_invoice':
                                    total_amount += move_before_90.amount_total
                                    total_paid += move_before_90.amount_total - move_before_90.amount_residual
                                elif move_before_90.move_type == 'out_refund':
                                    total_amount += -(move_before_90.amount_total)
                                    total_paid += -(move_before_90.amount_total - move_before_90.amount_residual)
                            total_balance = total_amount - total_paid
                            rec.sh_customer_sixty_to_ninety = total_balance
                        if moves_90_plus:
                            total_paid = 0.0
                            total_amount = 0.0
                            total_balance = 0.0
                            for move_90_plus in moves_90_plus:
                                if move_90_plus.move_type == 'out_invoice':
                                    total_amount += move_90_plus.amount_total
                                    total_paid += move_90_plus.amount_total - move_90_plus.amount_residual
                                elif move_90_plus.move_type == 'out_refund':
                                    total_amount += -(move_90_plus.amount_total)
                                    total_paid += -(move_90_plus.amount_total - move_90_plus.amount_residual)
                            total_balance = total_amount - total_paid
                            rec.sh_customer_ninety_plus = total_balance
                        rec.sh_customer_total = rec.sh_customer_zero_to_thiry + rec.sh_customer_thirty_to_sixty + \
                            rec.sh_customer_sixty_to_ninety + rec.sh_customer_ninety_plus
                    overdue_moves = False
                    if self.env.company.sh_display_due_statement == 'due':
                        overdue_moves = moves.filtered(
                            lambda x: x.invoice_date_due and x.invoice_date_due
                            >= fields.Date.today(
                            ) and x.amount_residual > 0.00)
                    elif self.env.company.sh_display_due_statement == 'overdue':
                        overdue_moves = moves.filtered(
                            lambda x: x.invoice_date_due and x.invoice_date_due
                            < fields.Date.today() and x.amount_residual > 0.00)
                    elif self.env.company.sh_display_due_statement == 'both':
                        overdue_moves = moves.filtered(
                            lambda x: x.amount_residual > 0.00)
                    if overdue_moves:
                        rec.sh_customer_due_statement_ids.unlink()
                        overdue_statement_lines = []
                        for overdue in overdue_moves:
                            overdue_statement_vals = {
                                'sh_account':
                                rec.property_account_receivable_id.name,
                                'currency_id': overdue.currency_id.id,
                                'name': overdue.name,
                                'customer_ref': overdue.po_no,
                                'sh_today': fields.Date.today(),
                                'sh_due_customer_invoice_date':
                                overdue.invoice_date,
                                'sh_due_customer_due_date':
                                overdue.invoice_date_due,
                            }
                            if overdue.move_type == 'out_invoice':
                                overdue_statement_vals.update({
                                    'sh_due_customer_amount': overdue.amount_total,
                                    'sh_due_customer_paid_amount': overdue.amount_total - overdue.amount_residual,
                                    'sh_due_customer_balance': overdue.amount_total - (overdue.amount_total - overdue.amount_residual),
                                })
                            elif overdue.move_type == 'out_refund':
                                overdue_statement_vals.update({
                                    'sh_due_customer_amount': -(overdue.amount_total),
                                    'sh_due_customer_paid_amount': -(overdue.amount_total - overdue.amount_residual),
                                    'sh_due_customer_balance': -(overdue.amount_total - (overdue.amount_total - overdue.amount_residual)),
                                })
                            overdue_statement_lines.append(
                                (0, 0, overdue_statement_vals))
                        rec.sh_customer_due_statement_ids = overdue_statement_lines
                if rec.supplier_rank > 0:
                    rec.sh_vendor_statement_ids = False
                    rec.sh_vendor_due_statement_ids = False
                    moves = self.env['account.move'].sudo().search([
                        ('partner_id', '=', rec.id),
                        ('move_type', 'in', ['in_invoice', 'in_refund']),
                        ('state', 'not in', ['draft', 'cancel']), ('is_proforma_invoice', '=', False)
                    ])
                    if moves:
                        rec.sh_vendor_statement_ids.unlink()
                        statement_lines = []
                        for move in moves:
                            vals = {
                                'sh_account':
                                rec.property_account_payable_id.name,
                                'name': move.name,
                                'currency_id': move.currency_id.id,
                                'sh_vendor_invoice_date': move.invoice_date,
                                'sh_vendor_due_date': move.invoice_date_due,
                            }
                            if move.move_type == 'in_refund':
                                vals.update({
                                    'sh_vendor_amount': -(move.amount_total),
                                    'sh_vendor_paid_amount': -(move.amount_total - move.amount_residual),
                                    'sh_vendor_balance': -(move.amount_total - (move.amount_total - move.amount_residual)),
                                    })
                            elif move.move_type == 'in_invoice':
                                vals.update({
                                    'sh_vendor_amount': move.amount_total,
                                    'sh_vendor_paid_amount': move.amount_total - move.amount_residual,
                                    'sh_vendor_balance': move.amount_total - (move.amount_total - move.amount_residual),
                                    })
                            statement_lines.append((0, 0, vals))
                        rec.sh_vendor_statement_ids = statement_lines
                        today = fields.Date.today()
                        rec.sh_vendor_zero_to_thiry = 0.0
                        rec.sh_vendor_thirty_to_sixty = 0.0
                        rec.sh_vendor_sixty_to_ninety = 0.0
                        rec.sh_vendor_ninety_plus = 0.0
                        date_before_30 = today - timedelta(days=30)
                        date_before_60 = date_before_30 - \
                            timedelta(days=30)
                        date_before_90 = date_before_60 - \
                            timedelta(days=30)
                        moves_before_30_days = self.env['account.move'].sudo(
                        ).search([('move_type', 'in',
                                   ['in_invoice', 'in_refund']),
                                  ('partner_id', '=', rec.id),
                                  ('is_proforma_invoice', '=', False),
                                  ('invoice_date', '>=', date_before_30),
                                  ('invoice_date', '<=', fields.Date.today()),
                                  ('state', 'not in', ['draft', 'cancel'])])
                        moves_before_60_days = self.env['account.move'].sudo(
                        ).search([('move_type', 'in',
                                   ['in_invoice', 'in_refund']),
                                  ('partner_id', '=', rec.id),
                                  ('is_proforma_invoice', '=', False),
                                  ('invoice_date', '>=', date_before_60),
                                  ('invoice_date', '<=', date_before_30)])
                        moves_before_90_days = self.env['account.move'].sudo(
                        ).search([('move_type', 'in',
                                   ['in_invoice', 'in_refund']),
                                  ('partner_id', '=', rec.id),
                                  ('is_proforma_invoice', '=', False),
                                  ('invoice_date', '>=', date_before_90),
                                  ('invoice_date', '<=', date_before_60),
                                  ('state', 'not in', ['draft', 'cancel'])])
                        moves_90_plus = self.env['account.move'].sudo().search(
                            [('move_type', 'in', ['in_invoice', 'in_refund']),
                             ('partner_id', '=', rec.id),
                             ('is_proforma_invoice', '=', False),
                             ('invoice_date', '<=', date_before_90),
                             ('state', 'not in', ['draft', 'cancel'])])
                        if moves_before_30_days:
                            total_paid = 0.0
                            total_amount = 0.0
                            total_balance = 0.0
                            for move_before_30 in moves_before_30_days:
                                if move_before_30.move_type == 'in_refund':
                                    total_amount += -(move_before_30.amount_total)
                                    total_paid += -(move_before_30.amount_total - move_before_30.amount_residual)
                                elif move_before_30.move_type == 'in_invoice':
                                    total_amount += move_before_30.amount_total
                                    total_paid += move_before_30.amount_total - move_before_30.amount_residual
                            total_balance = total_amount - total_paid
                            rec.sh_vendor_zero_to_thiry = total_balance
                        if moves_before_60_days:
                            total_paid = 0.0
                            total_amount = 0.0
                            total_balance = 0.0
                            for move_before_60 in moves_before_60_days:
                                if move_before_60.move_type == 'in_refund':
                                    total_amount += -(move_before_60.amount_total)
                                    total_paid += -(move_before_60.amount_total - move_before_60.amount_residual)
                                elif move_before_60.move_type == 'in_invoice':
                                    total_amount += move_before_60.amount_total
                                    total_paid += move_before_60.amount_total - move_before_60.amount_residual
                            total_balance = total_amount - total_paid
                            total_balance = total_amount - total_paid
                            rec.sh_vendor_thirty_to_sixty = total_balance
                        if moves_before_90_days:
                            total_paid = 0.0
                            total_amount = 0.0
                            total_balance = 0.0
                            for move_before_90 in moves_before_90_days:
                                if move_before_90.move_type == 'in_refund':
                                    total_amount += -(move_before_90.amount_total)
                                    total_paid += -(move_before_90.amount_total - move_before_90.amount_residual)
                                elif move_before_90.move_type == 'in_invoice':
                                    total_amount += move_before_90.amount_total
                                    total_paid += move_before_90.amount_total - move_before_90.amount_residual
                            total_balance = total_amount - total_paid
                            rec.sh_vendor_sixty_to_ninety = total_balance
                        if moves_90_plus:
                            total_paid = 0.0
                            total_amount = 0.0
                            total_balance = 0.0
                            for move_90_plus in moves_90_plus:
                                if move_90_plus.move_type == 'in_refund':
                                    total_amount += -(move_90_plus.amount_total)
                                    total_paid += -(move_90_plus.amount_total - move_90_plus.amount_residual)
                                elif move_90_plus.move_type == 'in_invoice':
                                    total_amount += move_90_plus.amount_total
                                    total_paid += move_90_plus.amount_total - move_90_plus.amount_residual
                            total_balance = total_amount - total_paid
                            rec.sh_vendor_ninety_plus = total_balance
                        rec.sh_vendor_total = rec.sh_vendor_zero_to_thiry + rec.sh_vendor_thirty_to_sixty + \
                            rec.sh_vendor_sixty_to_ninety + rec.sh_vendor_ninety_plus
                    else:
                        rec.sh_vendor_statement_ids = False
                    overdue_moves = False
                    if self.env.company.sh_display_due_statement == 'due':
                        overdue_moves = moves.filtered(
                            lambda x: x.invoice_date_due and x.invoice_date_due
                            >= fields.Date.today(
                            ) and x.amount_residual > 0.00)
                    elif self.env.company.sh_display_due_statement == 'overdue':
                        overdue_moves = moves.filtered(
                            lambda x: x.invoice_date_due and x.invoice_date_due
                            < fields.Date.today() and x.amount_residual > 0.00)
                    elif self.env.company.sh_display_due_statement == 'both':
                        overdue_moves = moves.filtered(
                            lambda x: x.amount_residual > 0.00)
                    if overdue_moves:
                        rec.sh_vendor_due_statement_ids.unlink()
                        overdue_statement_lines = []
                        for overdue in overdue_moves:
                            overdue_statement_vals = {
                                'sh_account':
                                rec.property_account_payable_id.name,
                                'name': overdue.name,
                                # 'customer_ref': overdue.po_no,
                                'currency_id': overdue.currency_id.id,
                                'sh_due_vendor_invoice_date':
                                overdue.invoice_date,
                                'sh_due_vendor_due_date':
                                overdue.invoice_date_due,
                                'sh_today': fields.Date.today(),
                            }
                            if overdue.move_type == 'in_refund':
                                overdue_statement_vals.update({
                                    'sh_due_vendor_amount': -(overdue.amount_total),
                                    'sh_due_vendor_paid_amount': -(overdue.amount_total - overdue.amount_residual),
                                    'sh_due_vendor_balance': -(overdue.amount_total - (overdue.amount_total - overdue.amount_residual)),
                                })
                            elif overdue.move_type == 'in_invoice':
                                overdue_statement_vals.update({
                                    'sh_due_vendor_amount': overdue.amount_total,
                                    'sh_due_vendor_paid_amount': overdue.amount_total - overdue.amount_residual,
                                    'sh_due_vendor_balance': overdue.amount_total - (overdue.amount_total - overdue.amount_residual),
                                })
                            overdue_statement_lines.append(
                                (0, 0, overdue_statement_vals))

                        rec.sh_vendor_due_statement_ids = overdue_statement_lines
                    else:
                        rec.sh_vendor_due_statement_ids = False

    def get_combined_statements(self):
        combine_list = []
        for cust_statement in self.sh_customer_statement_ids:
            if cust_statement.sh_customer_amount != cust_statement.sh_customer_paid_amount:
                combine_list.append({
                    'sh_account': cust_statement.sh_account,
                    'name': cust_statement.name,
                    'customer_ref': cust_statement.customer_ref,
                    'currency_id': cust_statement.currency_id.name,
                    'sh_customer_invoice_date': cust_statement.sh_customer_invoice_date,
                    'sh_customer_due_date': cust_statement.sh_customer_due_date,
                    'sh_customer_amount': cust_statement.sh_customer_amount,
                    'sh_customer_paid_amount': cust_statement.sh_customer_paid_amount,
                    'sh_customer_balance': cust_statement.sh_customer_balance,

                })
        for cust_overdue_statement in self.sh_customer_due_statement_ids:
            if cust_overdue_statement.sh_due_customer_amount != cust_overdue_statement.sh_due_customer_paid_amount:
                combine_list.append({
                    'sh_account': cust_overdue_statement.sh_account,
                    'name': cust_overdue_statement.name,
                    'customer_ref': cust_overdue_statement.customer_ref,
                    'currency_id': cust_overdue_statement.currency_id.name,
                    'sh_customer_invoice_date': cust_overdue_statement.sh_due_customer_invoice_date,
                    'sh_customer_due_date': cust_overdue_statement.sh_due_customer_due_date,
                    'sh_customer_amount': cust_overdue_statement.sh_due_customer_amount,
                    'sh_customer_paid_amount': cust_overdue_statement.sh_due_customer_paid_amount,
                    'sh_customer_balance': cust_overdue_statement.sh_due_customer_balance

                })
        sorted_combine_list = sorted(combine_list, key=lambda x: x['sh_customer_invoice_date'])
        return sorted_combine_list                  


class OdesPartnerInvoice(models.Model):
    _inherit = "odes.partner.invoice"
    
    def view_detail(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("iconnexion_mccoy_custom.action_iconnexion_mccoy_moves_all_tree")
        years = self.year
        date_start = years+'-01-01'
        date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
        date_end = years+'-12-31'
        date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
        domain_invoice = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('partner_id', 'child_of', self.partner_id.id),
            ('date', '>=', date_start),
            ('date', '<=', date_end)
        ]
        move_obj = self.env["account.move"]
        move_ids = move_obj.search(domain_invoice).ids
        action['domain'] = [
            ('id', 'in', move_ids),
        ]
        return action


## Community-safe: sh.customer.statement models are not available in this stack.
