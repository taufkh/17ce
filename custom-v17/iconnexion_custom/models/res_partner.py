# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.addons.base.models.res_partner import WARNING_HELP, WARNING_MESSAGE
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.osv import expression


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.depends('country_id')
    @api.depends_context('company')
    def _compute_product_pricelist(self):
        company = self.env.company.id
        res = self.env['product.pricelist']._get_partner_pricelist_multi(self.ids, company_id=company)
        for p in self:
            p.property_product_pricelist = res.get(p.id)
            if not p._origin.id :
                if self.env.company.property_product_pricelist:
                    p.property_product_pricelist = self.env.company.property_product_pricelist.id
                    
    bill_to_contact_person_id = fields.Many2one('res.partner',string="Bill-to Contact Person")
    bill_to_street = fields.Char('Bill-to Street')
    bill_to_block = fields.Char('Bill-to Block')
    bill_to_city = fields.Char('Bill-to City')
    bill_to_zip = fields.Char('Bill-to Zip')
    bill_to_state = fields.Char('Bill-to State')
    bill_to_country_id = fields.Many2one('res.country',string="Bill-to Country")
    bill_to_remarks = fields.Char('Bill-to Remarks')

    bill_to_contact_person2_id = fields.Many2one('res.partner',string="Bill-to Contact Person (2)")
    bill_to_street2 = fields.Char('Bill-to Street (2)')
    bill_to_block2 = fields.Char('Bill-to Block (2)')
    bill_to_city2 = fields.Char('Bill-to City (2)')
    bill_to_zip2 = fields.Char('Bill-to Zip (2)')
    bill_to_state2 = fields.Char('Bill-to State (2)')
    bill_to_country2_id = fields.Many2one('res.country',string="Bill-to Country (2)")
    bill_to_remarks2 = fields.Char('Bill-to Remarks (2)')

    bill_to_contact_person3_id = fields.Many2one('res.partner',string="Bill-to Contact Person (3)")
    bill_to_street3 = fields.Char('Bill-to Street (3)')
    bill_to_block3 = fields.Char('Bill-to Block (3)')
    bill_to_city3 = fields.Char('Bill-to City (3)')
    bill_to_zip3 = fields.Char('Bill-to Zip (3)')
    bill_to_state3 = fields.Char('Bill-to State (3)')
    bill_to_country3_id = fields.Many2one('res.country',string="Bill-to Country (3)")
    bill_to_remarks3 = fields.Char('Bill-to Remarks (3)')

    bill_to_contact_person4_id = fields.Many2one('res.partner',string="Bill-to Contact Person (4)")
    bill_to_street4 = fields.Char('Bill-to Street (4)')
    bill_to_block4 = fields.Char('Bill-to Block (4)')
    bill_to_city4 = fields.Char('Bill-to City (4)')
    bill_to_zip4 = fields.Char('Bill-to Zip (4)')
    bill_to_state4 = fields.Char('Bill-to State (4)')
    bill_to_country4_id = fields.Many2one('res.country',string="Bill-to Country (4)")
    bill_to_remarks4 = fields.Char('Bill-to Remarks (4)')

    ship_to_contact_person_id = fields.Many2one('res.partner',string="Ship-to Contact Person")
    ship_to_street = fields.Char('Ship-to Street')
    ship_to_block = fields.Char('Ship-to Block')
    ship_to_city = fields.Char('Ship-to City')
    ship_to_zip = fields.Char('Ship-to Zip')
    ship_to_state = fields.Char('Ship-to State')
    ship_to_country_id = fields.Many2one('res.country',string="Ship-to Country")
    ship_to_remarks = fields.Char('Ship-to Remarks')

    ship_to_contact_person2_id = fields.Many2one('res.partner',string="Ship-to Contact Person (2)")
    ship_to_street2 = fields.Char('Ship-to Street (2)')
    ship_to_block2 = fields.Char('Ship-to Block (2)')
    ship_to_city2 = fields.Char('Ship-to City (2)')
    ship_to_zip2 = fields.Char('Ship-to Zip (2)')
    ship_to_state2 = fields.Char('Ship-to State (2)')
    ship_to_country2_id = fields.Many2one('res.country',string="Ship-to Country (2)")
    ship_to_remarks2 = fields.Char('Ship-to Remarks (2)')

    ship_to_contact_person3_id = fields.Many2one('res.partner',string="Ship-to Contact Person (3)")
    ship_to_street3 = fields.Char('Ship-to Street (3)')
    ship_to_block3 = fields.Char('Ship-to Block (3)')
    ship_to_city3 = fields.Char('Ship-to City (3)')
    ship_to_zip3 = fields.Char('Ship-to Zip (3)')
    ship_to_state3 = fields.Char('Ship-to State (3)')
    ship_to_country3_id = fields.Many2one('res.country',string="Ship-to Country (3)")
    ship_to_remarks3 = fields.Char('Ship-to Remarks (3)')

    ship_to_contact_person4_id = fields.Many2one('res.partner',string="Ship-to Contact Person (4)")
    ship_to_street4 = fields.Char('Ship-to Street (4)')
    ship_to_block4 = fields.Char('Ship-to Block (4)')
    ship_to_city4 = fields.Char('Ship-to City (4)')
    ship_to_zip4 = fields.Char('Ship-to Zip (4)')
    ship_to_state4 = fields.Char('Ship-to State (4)')
    ship_to_country4_id = fields.Many2one('res.country',string="Ship-to Country (4)")
    ship_to_remarks4 = fields.Char('Ship-to Remarks (4)')

    sales_history_ids = fields.One2many('icon.sales.history','partner_id', string="Sales History")
    old_sales_history_ids = fields.One2many('icon.old.sales.history', 'partner_id', string="Old Sales History")
    old_quote_history_ids = fields.One2many('icon.old.quote.history', 'partner_id', string="Old Quotation History")
    email_icon = fields.Char("Email Iconnexion")
    #1 each sales can only view customer assign
    #2 if adarsh report to Jijo, then jijo can view adarsh contact
    #3 sales hod role can view all sales

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        """
        Overrides orm field_view_get.
        @return: Dictionary of Fields, arch and toolbar.
        """

        arch, view = super()._get_view(view_id, view_type, **options)
        # export_xlsx="0"
        if self.user_has_groups('iconnexion_custom.group_iconnexion_sales_user'):           
            export_true = """<tree string="Contacts" sample="1" multi_edit="1" export_xlsx="0">"""
            arch = arch.replace(str("""<tree string="Contacts" sample="1" multi_edit="1" export_xlsx="1">"""),export_true )
        
        return arch, view

    def _get_name(self):
        """ Utility method to allow name_get to be overrided without re-browse the partner """
        partner = self
        name = partner.name or ''

        if partner.company_name or partner.parent_id:
            if not name and partner.type in ['invoice', 'delivery', 'other']:
                name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
            if not partner.is_company:
                if self.company_id :  #disable for icon company
                    trading_company_id = int(self.env['ir.config_parameter'].sudo().get_param('iconnexion_custom.trading_company_id', '3') or 0)
                    if self.company_id.id != trading_company_id:
                        name = self._get_contact_name(partner, name)

        if self._context.get('show_address_only'):
            name = partner._display_address(without_company=True)
        if self._context.get('show_address'):
            name = name + "\n" + partner._display_address(without_company=True)
        name = name.replace('\n\n', '\n')
        name = name.replace('\n\n', '\n')
        if self._context.get('address_inline'):
            name = name.replace('\n', ', ')
        if self._context.get('show_email') and partner.email:
            name = "%s <%s>" % (name, partner.email)
        if self._context.get('html_format'):
            name = name.replace('\n', '<br/>')
        if self._context.get('show_vat') and partner.vat:
            name = "%s ‒ %s" % (name, partner.vat)
        if self.customer_code:
            name = '[%s] %s' % (self.customer_code, name)
        return name


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100):
        if self.user_has_groups('iconnexion_custom.group_iconnexion_sales_hod'):
            return super(Partner, self)._name_search(name, args, operator, limit)
        
        # _name_search = super(Partner, self)._name_search(name, args=args, operator=operator, limit=limit)
        if self._context.get('disable_search'):
            if args is None:
                args = []
            report_to_user_ids = self.env.user.report_to_user_ids
            r_ids = [ n.id for n in report_to_user_ids]
            user_domain = [self.env.user.id]
            if r_ids:
                
                for r in r_ids:
                    user_domain.append(r)
            # args += [('user_id','in',user_domain)]
            selected_companies = self.env['res.company'].browse(self._context.get('allowed_company_ids'))
            active_company = self.env.user.company_id.id
            _cross_co_ids = [int(x) for x in (self.env['ir.config_parameter'].sudo().get_param('iconnexion_custom.cross_company_partner_ids', '1,2') or '1,2').split(',') if x.strip()]
            _main_co_id = _cross_co_ids[0] if _cross_co_ids else 1
            if self.env.company.id in _cross_co_ids:  # v16: replaced hardcoded [2, 1] with ir.config_parameter
                if args:
                    args += ['|','|',('company_id','=',_main_co_id),('company_id','=',False),('user_id','in',user_domain)]
            else:
                args += [('user_id','in',user_domain)]
            return super(Partner, self)._name_search(name, args=args, operator=operator, limit=limit)
        
        return super(Partner, self)._name_search(name, args=args, operator=operator, limit=limit)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self._context
        ctx = {'disable_search': True}
        # if self._context.get('disable_search'): 
        allow_search = True
        if args:
            for arg in args:
                if arg[0] == 'signup_token':
                    allow_search = False


        if ctx.get('disable_search') and allow_search:
            if self.user_has_groups('iconnexion_custom.group_iconnexion_sales_hod'):
                return super(Partner, self).search(args, offset=offset,  limit=limit, order=order, count=count)
            
            report_to_user_ids = self.env.user.report_to_user_ids
            
            #tambahkan domain, semua vendor bisa di akses
            # jadi user ini bisa lihat partner yang di bawah nya atau vendor

            r_ids = [ n.id for n in report_to_user_ids]
            user_domain = [self.env.user.id]
            if r_ids:
                
                for r in r_ids:
                    user_domain.append(r)
            selected_companies = self.env['res.company'].browse(self._context.get('allowed_company_ids'))
            active_company = self.env.user.company_id.id
            _cross_co_ids = [int(x) for x in (self.env['ir.config_parameter'].sudo().get_param('iconnexion_custom.cross_company_partner_ids', '1,2') or '1,2').split(',') if x.strip()]
            _main_co_id = _cross_co_ids[0] if _cross_co_ids else 1
            if self.env.company.id in _cross_co_ids:  # v16: replaced hardcoded [2, 1] with ir.config_parameter
                args += ['|','|',('company_id','=',_main_co_id),('company_id','=',False),('user_id','in',user_domain)]
            else:
                args += ['|',('user_id','in',user_domain),('supplier_rank','>', 0)]
        res = super(Partner, self).search(args, offset=offset, limit=limit, order=order, count=count)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        ctx = {'disable_search': True}
        # if self._context.get('disable_search'):  
        if ctx.get('disable_search'):
            if self.user_has_groups('iconnexion_custom.group_iconnexion_sales_hod'):
                return super(Partner, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
            report_to_user_ids = self.env.user.report_to_user_ids
            r_ids = [ n.id for n in report_to_user_ids]
            user_domain = [self.env.user.id]
            if r_ids:                
                for r in r_ids:
                    user_domain.append(r)
            # domain += [('user_id','in',user_domain)]
            selected_companies = self.env['res.company'].browse(self._context.get('allowed_company_ids'))
            active_company = self.env.user.company_id.id
            _cross_co_ids = [int(x) for x in (self.env['ir.config_parameter'].sudo().get_param('iconnexion_custom.cross_company_partner_ids', '1,2') or '1,2').split(',') if x.strip()]
            _main_co_id = _cross_co_ids[0] if _cross_co_ids else 1
            if self.env.company.id in _cross_co_ids:  # v16: replaced hardcoded [2, 1] with ir.config_parameter
                domain += ['|','|',('company_id','=',_main_co_id),('company_id','=',False),('user_id','in',user_domain)]
            else:
                domain += [('user_id','in',user_domain)]

        res = super(Partner, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res

    # def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
    #     if self._context.get('disable_search'):    
    #         print ('sukseserserserserserser',domain)  
    #         if self.user_has_groups('iconnexion_custom.group_iconnexion_sales_hod'):
    #             return super(Partner, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

    #         # domain = expression.AND([domain, [('user_id', '=', self.env.user.id)]])   
    #         report_to_user_ids = self.env.user.report_to_user_ids
    #         r_ids = [ n.id for n in report_to_user_ids]
            
    #         if r_ids:
    #             user_domain = [self.env.user.id]
    #             for r in r_ids:
    #                 user_domain.append(r)
                   
    #             domain = expression.AND([domain, [('user_id', 'in', tuple(user_domain))]])
    #             return super(Partner, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

    #         domain = expression.AND([domain, [('user_id', '=', self.env.user.id)]])  
    #     return super(Partner, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

# v16: sh.customer.statement model not available (third-party module not installed); class disabled
# class CustomerStateMent(models.Model):
#     _inherit = 'sh.customer.statement'
#     icon_customer_amount = fields.Float('Total Amount', compute='_compute_total_amount')
#     icon_customer_paid_amount = fields.Float('Paid Amount', compute='_compute_paid_amount')
#     icon_customer_balance = fields.Float('Customer Balance', compute='_compute_balance')
#     def _compute_total_amount(self):
#         for data in self: data.icon_customer_amount = data.sh_customer_amount
#     def _compute_paid_amount(self):
#         for data in self: data.icon_customer_paid_amount = data.sh_customer_paid_amount
#     def _compute_balance(self):
#         for data in self: data.icon_customer_balance = data.sh_customer_balance
