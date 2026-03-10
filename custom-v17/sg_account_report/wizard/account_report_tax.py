# See LICENSE file for full copyright and licensing details.

from odoo import models


class AccountTaxReport(models.TransientModel):
    _name = 'account.tax.report'
    _description = 'Tax Report Wizard (Compatibility)'
    _inherit = 'account.common.report'

    def _print_report(self, data):
        return self.env.ref(
            'sg_account_report.'
            'action_report_account_tax').report_action(self, data=data)
