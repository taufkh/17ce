from odoo import models, fields, api, _


class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"

    @api.model
    def _build_lines_hierarchy(self, options_list, financial_lines, solver, groupby_keys):
        ''' Travel the whole hierarchy and create the report lines to be rendered.
        :param options_list:        The report options list, first one being the current dates range, others being the
                                    comparisons.
        :param financial_lines:     An account.financial.html.report.line recordset.
        :param solver:              The FormulaSolver instance used to compute the formulas.
        :param groupby_keys:        The sorted encountered keys in the solver.
        :return:                    The lines.
        '''
        lines = []
        for financial_line in financial_lines:

            is_leaf = solver.is_leaf(financial_line)
            has_lines = solver.has_move_lines(financial_line)

            financial_report_line = self._get_financial_line_report_line(
                options_list[0],
                financial_line,
                solver,
                groupby_keys,
            )

            # Manage 'hide_if_zero' field.
            if financial_line.hide_if_zero and all(self.env.company.currency_id.is_zero(column['no_format'])
                                                   for column in financial_report_line['columns'] if 'no_format' in column):
                continue

            # Manage 'hide_if_empty' field.
            if financial_line.hide_if_empty and is_leaf and not has_lines:
                continue

            lines.append(financial_report_line)

            aml_lines = []
            if financial_line.children_ids:
                # Travel children.
                lines += self._build_lines_hierarchy(options_list, financial_line.children_ids, solver, groupby_keys)
            elif is_leaf and financial_report_line['unfolded']:
                # Fetch the account.move.lines.
                solver_results = solver.get_results(financial_line)
                for groupby_id, display_name, results in financial_line._compute_amls_results(options_list, sign=solver_results['amls']['sign']):
                    aml_lines.append(self._get_financial_aml_report_line(
                        options_list[0],
                        financial_line,
                        groupby_id,
                        display_name,
                        results,
                        groupby_keys,
                    ))
            lines += aml_lines

            if self.env.company.totals_below_sections and (financial_line.children_ids or (is_leaf and financial_report_line['unfolded'] and aml_lines)):
                lines.append(self._get_financial_total_section_report_line(options_list[0], financial_report_line))
                financial_report_line["unfolded"] = True  # enables adding "o_js_account_report_parent_row_unfolded" -> hides total amount in head line as it is displayed later in total line
        for line in lines :
            if not isinstance(line, dict):
                    continue
            line_id = line['id']
            if not line_id or not isinstance(line_id, str) or '_' not in line_id:
                    continue
            part = line_id.split('_')
            id_obj = part[-1]
            account_obj = self.env['account.account'].search([('id', '=', id_obj)])
            if not account_obj:
                continue
            line.update({
                'account_id': account_obj.id,
                'is_clearing': account_obj.is_clearing,
            })
        return lines