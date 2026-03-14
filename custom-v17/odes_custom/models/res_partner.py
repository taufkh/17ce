# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP


class ResPartner(models.Model):
    _inherit = 'res.partner'

    contact_person = fields.Char('Contact Person')
    contact_number = fields.Char('Contact Number')
    freight_terms = fields.Char('Freight Terms')

    property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
        string="Account Payable",
        domain="[('account_type', '=', 'liability_payable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
        help="This account will be used instead of the default one as the payable account for the current partner",
        required=False)
    property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
        string="Account Receivable",
        domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
        help="This account will be used instead of the default one as the receivable account for the current partner",
        required=False)

    is_zip = fields.Boolean('Zip Only', default=False)

    @api.onchange('country_id')
    def _onchange_country_odes(self):
        self.is_zip = self.country_id.is_zip
        if self.country_id:
            if self.country_id.property_payment_term_id:
                self.property_payment_term_id = self.country_id.property_payment_term_id
        self.freight_terms = self.country_id.freight_terms

    def action_view_projects(self):
        self.ensure_one()

        context = dict(self.env.context or {})
        target = 'self'
        print('==================== Partner ====================')
        print(self)
        print(self.id)
        print('============================================\n\n\n')

        return {
            'name': 'Projects',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'project.project',
            'domain': [('partner_id', '=', self.id)],
            'target': target
        }

    def action_view_invoices_sgd(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("odes_custom.action_move_out_invoice_type_sgd")
        action['domain'] = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('partner_id', 'child_of', self.id),
        ]
        action['context'] = {'default_move_type':'out_invoice', 'move_type':'out_invoice', 'journal_type': 'sale', 'search_default_unpaid': 1}
        return action

    projects_count = fields.Integer(compute='_compute_projects_count', string='Projects Count')
    invoices_count = fields.Integer(compute='_compute_invoices_count', string='Invoices Count')
    sgd_currency_id = fields.Many2one('res.currency', compute='_compute_sgd_currency', readonly=True,
        string="SGD Currency", help='Utility field to express amount currency')
    # sgd_total_invoiced =
    sgd_total_invoiced = fields.Monetary(compute='_compute_invoice_total_sgd', string="Total Invoiced (SGD)", groups='account.group_account_invoice,account.group_account_readonly')

    def _compute_invoice_total_sgd(self):
        self.total_invoiced = 0
        if not self.ids:
            return True

        all_partners_and_children = {}
        all_partner_ids = []
        for partner in self.filtered('id'):
            # price_total is in the company currency
            all_partners_and_children[partner] = self.with_context(active_test=False).search([('id', 'child_of', partner.id)]).ids
            all_partner_ids += all_partners_and_children[partner]

        domain = [
            ('partner_id', 'in', all_partner_ids),
            ('state', 'not in', ['draft', 'cancel']),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
        ]
        price_totals = self.env['account.invoice.report'].read_group(domain, ['price_subtotal'], ['partner_id'])
        # price_totals = self.env['account.move'].search(domain)
        print('==================== Invoices ==================I==')
        print(price_totals)
        for price in price_totals:
            print(price['price_subtotal'])
        print('============================================\n\n\n')
        for partner, child_ids in all_partners_and_children.items():
            partner.sgd_total_invoiced = sum(price['price_subtotal'] for price in price_totals if price['partner_id'][0] in child_ids)

    def _compute_sgd_currency(self):
        for partner in self:
            partner.sgd_currency_id = self.env['res.currency'].sudo().search([('name', '=', "SGD")])

    def _compute_projects_count(self):
        for partner in self:
            partner.projects_count = self.env['project.project'].sudo().search_count([('partner_id', '=', self.id)])

    def _compute_invoices_count(self):
        for partner in self:
            partner.invoices_count = 1

class ResCountry(models.Model):
    _inherit = "res.country"

    is_zip = fields.Boolean('Zip Only', default=False)
    property_payment_term_id = fields.Many2one('account.payment.term', 'Payment Terms')
    freight_terms = fields.Char('Freight Terms')
    tax_ids = fields.Many2many('account.tax','country_tax_rel','res_country_id','account_tax_rel',string='Customer Taxess')
