from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        res = super().session_info()
        if request.env.user.has_group('base.group_user'):
            company_id = res.get('company_id')
            if company_id:
                company = request.env['res.company'].browse(company_id)
                res['company_currency_id'] = company.currency_id.id
            else:
                res['company_currency_id'] = None
            res['companies_currency_id'] = {
                company.id: company.currency_id.id for company in request.env.user.company_ids
            }
        return res

