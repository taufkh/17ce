# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class ResPartner(models.Model):
    _inherit = "res.partner"

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

    def write(self, vals):
        if vals.get('name'):
            lock_companies = self._get_companies_from_config('odes_sign.partner_name_lock_company_refs')
            for partner in self:
                must_lock = (
                    partner.sale_order_count > 0 and (
                        not partner.company_id or
                        (lock_companies and partner.company_id in lock_companies) or
                        (not lock_companies and partner.company_id == self.env.company)
                    )
                )
                if must_lock:
                    raise UserError(("There's already a so/invoice attached, please use the change name button"))
        
        result = super(ResPartner, self).write(vals)
        return result
