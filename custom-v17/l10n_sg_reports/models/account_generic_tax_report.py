from odoo import models


class GenericTaxReport(models.AbstractModel):
    _inherit = 'account.generic.tax.report'

    def _get_total_line_eval_dict(self, period_balances_by_code, period_date_from, period_date_to, options):
        eval_dict = super()._get_total_line_eval_dict(
            period_balances_by_code, period_date_from, period_date_to, options
        )
        if self.env.company.country_id.code == 'SG':
            net_profit = 0.0
            try:
                self.env.cr.execute(
                    """
                    SELECT COALESCE(-SUM(aml.balance), 0.0)
                    FROM account_move_line aml
                    JOIN account_move move ON move.id = aml.move_id
                    JOIN account_account account ON account.id = aml.account_id
                    WHERE move.company_id = %s
                      AND aml.date >= %s
                      AND aml.date <= %s
                      AND (%s OR move.state = 'posted')
                      AND account.account_type IN ('income', 'income_other', 'expense', 'expense_depreciation', 'expense_direct_cost')
                    """,
                    (self.env.company.id, period_date_from, period_date_to, options.get('all_entries', False)),
                )
                row = self.env.cr.fetchone() or (0.0,)
                net_profit = row[0] or 0.0
            except Exception:
                net_profit = 0.0
            eval_dict['net_profit'] = net_profit
        return eval_dict

