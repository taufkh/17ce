# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import api, fields, models, _, Command
from odoo.tools.misc import clean_context
from odoo.tools.safe_eval import safe_eval

from odoo.exceptions import ValidationError
from math import floor


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    sample_status = fields.Selection([
        ('not_requested', 'Not Requested'),
        ('requested', 'Requested'),
        ('shipped', 'Shipped'),
        ('received', 'Received'),
        ('rejected', 'Rejected')
    ], string='Sample Status', default='not_requested', copy=False, tracking=True)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    override_pi_block = fields.Boolean(string="Override PI Payment Block", groups="sales_team.group_sale_manager", copy=False, default=False, tracking=True)

    def unlink(self):
        for rec in self:
            if rec.invoice_ids:
                raise ValidationError("Cannot delete Sales Order: Proforma Invoice(s) found.")
        return super().unlink()

    def _get_invoiceable_lines(self, final=False):
        if self.state == 'draft':
            return self.order_line
        else:
            return super()._get_invoiceable_lines(final=final)

    def create_proforma_invoice(self):
        ctx = self._context.copy()
        ctx['raise_if_nothing_to_invoice'] = False
        for rec in self:
            # if rec.state == 'draft':
                moves = rec.with_context(ctx)._create_invoices()
                for line in moves.invoice_line_ids:
                    line.quantity = sum(line.sale_line_ids.mapped('product_uom_qty'))
                
                if moves:
                    context = clean_context(rec._context)
                    if len(rec.company_id) == 1:
                        # All orders are in the same company
                        rec.order_line.sudo().with_context(context).with_company(rec.company_id)._timesheet_service_generation()
                    else:
                        # Orders from different companies are confirmed together
                        for order in rec:
                            order.order_line.sudo().with_context(context).with_company(order.company_id)._timesheet_service_generation()

    def action_confirm(self):
        # check is_paid on related invoices
        for rec in self:
            for invoice in rec.invoice_ids:
                if not rec.override_pi_block and not invoice.is_paid:
                    raise ValidationError("Cannot confirm Sales Order: Proforma Invoice is not paid.")
            if not rec.invoice_ids:
                raise ValidationError("Cannot confirm Sales Order: No Proforma Invoice found.")
            
            if rec.need_validation:
                raise ValidationError('Approval required to confirm this Sale Order.')

        res = super().action_confirm()

        # set opportunity to won if not already won
        for rec in self.filtered(lambda x: x.opportunity_id):
            if rec.opportunity_id.active and rec.opportunity_id.probability != 100:
                rec.opportunity_id.action_set_won_rainbowman()
        
        return res

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    is_paid = fields.Boolean(string='Is Paid', compute='_compute_is_paid', store=True, tracking=True)
    year_project = fields.Integer(string="Year project", copy=False, compute="_compute_year_project", store=True)

    @api.depends('paid_date')
    def _compute_year_project(self):
        for record in self:
            val = 0
            project_ids = record.invoice_line_ids.mapped('sale_line_ids.project_id')
            if record.paid_date and project_ids:
                val = floor((record.paid_date - project_ids.date_start).days / 365 ) + 1
            record.year_project = val
            record.recompute_lines_agents_amount()

    def recompute_lines_agents_amount(self):
        self.mapped("invoice_line_ids").agent_ids._compute_amount()

    @api.depends('state', 'payment_state')
    def _compute_is_paid(self):
        for record in self:
            record.is_paid = record.state == 'posted' and record.payment_state == 'paid'
