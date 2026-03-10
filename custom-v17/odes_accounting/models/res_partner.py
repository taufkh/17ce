# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, api, fields, models, tools
from odoo.addons.bus.models.bus_presence import AWAY_TIMER
from odoo.addons.bus.models.bus_presence import DISCONNECTION_TIMER
from odoo.osv import expression
from datetime import datetime

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    """ Update partner to add a field about notification preferences. Add a generic opt-out field that can be used
       to restrict usage of automatic email templates. """
    _inherit = "res.partner"
    
    
    # def _get_contact(self):
    #     for res in self:
    #         contact = 0
    #         for x in partner_id:
    #             if x.child_ids.type != 'contact':
    #                 contact += x.name
    #         res.contact = contact

    @api.depends('invoice_ids', 'invoice_ids.date', 'invoice_ids.state', 'is_updated_data')
    def _get_partner_invoice(self):
        for partner in self:
            result = []
            if partner.id:
                self.env['odes.partner.invoice'].search([('partner_id', '=', partner.id)]).unlink()
                self.env.cr.execute("""
                    select sum(amount_total), DATE_PART('year', CAST(date AS DATE)),currency_id, partner_id from account_move where partner_id = %s group by DATE_PART('year', CAST(date AS DATE)), currency_id, partner_id;
                """,(partner.id,))
                result = self.env.cr.fetchall()
            aml_list = []
            for res in result:
                years = str(res[1]).replace(".0","")
                total = 0
                if res[0]:
                    total = float(res[0])
                aml_list.append((0, 0, {'total': total,'currency_id': res[2], 'year': years, 'partner_id': res[3]}))
            
            partner.aml_ids = aml_list

    fax = fields.Char(string="Fax")
    aml_ids = fields.One2many('odes.partner.invoice', 'partner_id', string='Yearly Annual Invoice', compute='_get_partner_invoice', store=True)
    is_updated_data = fields.Boolean('Updated Data')
    # contact = fields.Char('Contact', compute='_get_contact')
    
    

class OdesPartnerInvoice(models.Model):
    _name = "odes.partner.invoice"
    _description = "Odes Partner Invoice Summary"
    
    def view_detail(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("odes_accounting.action_odes_accounting_moves_all_tree")
        years = self.year
        date_start = years+'-01-01'
        date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
#        date_start = datetime.strftime(date_start, '%Y-%m-%d')
        date_end = years+'-12-31'
        date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
#        date_end = datetime.strftime(date_end, '%Y-%m-%d')
        print (date_start, date_end, 'ddd')
        domain_invoice = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('partner_id', 'child_of', self.partner_id.id),
            ('date', '>=', date_start),
            ('date', '<=', date_end)
        ]
        move_obj = self.env["account.move"]
        move_ids = move_obj.search(domain_invoice).ids
        action['domain'] = [
            ('move_id', 'in', move_ids),
            ('exclude_from_invoice_tab', '=', False),
            
#            ('date', '>=', date_end),
            
            
            
            
        ]
#        action['context'] = {'default_move_type':'out_invoice', 'move_type':'out_invoice', 'journal_type': 'sale', 'search_default_unpaid': 1}
        return action

    total = fields.Monetary('Total')
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id)
    partner_id = fields.Many2one('res.partner', 'Partner')
    year = fields.Char('Year')
