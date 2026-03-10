from odoo import models, fields, api
from datetime import datetime, timedelta
import calendar
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

class CashflowForecastXlsx(models.AbstractModel):
    _name = 'report.odes_cashflow_forecast.cashflow_forecast_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Cashflow Forecast XLSX Report'
    
    def generate_xlsx_report(self, workbook, data, wizard):
        acc_move_obj = self.env['account.move.line']
        forecast_obj = self.env['sale.invoice.forecast']
        
        months = []
        for obj in wizard:            
            sheet = workbook.add_worksheet()

            cell_format = workbook.formats[0]
            cell_format.set_border(1)
            
            bold = workbook.add_format({'bold': True, 'border': 1})
            title_header = workbook.add_format({'bold': True, 'underline': True, 'bg_color': '#fceb47', 'border': 1})
            table_header = workbook.add_format({'bold': True, 'bg_color': '#da9594', 'align': 'center', 'border': 1})
            left_border = workbook.add_format({'left': 1})
            right_border = workbook.add_format({'right': 1})
            table_content = workbook.add_format({'bold': False})
            sheet.set_column(0, 0, 40)


            #get fridays of the month
            c = calendar.Calendar(firstweekday=calendar.SUNDAY)
            year = obj.date.year
            month = obj.date.month

            i = 0
            while i < 3:
                monthcal = c.monthdatescalendar(year,month)
                fridays = [day for week in monthcal for day in week if \
                day.weekday() == calendar.FRIDAY and \
                day.month == month]

                monthfriday = [x for x in fridays if x >= obj.date]

                if monthfriday:
                    months.append(monthfriday)

                month += 1
                if month > 12:
                    year += 1
                    month = 1
                i += 1

            start_date = (months[0][0] + timedelta(days= -7)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            end_date = months[-1][-1].strftime(DEFAULT_SERVER_DATE_FORMAT)
            whole_invoices = acc_move_obj.search([('date_maturity','>',  start_date), ('date_maturity','<=', end_date), ('move_id.state', '=', 'posted'), ('move_id.company_id','=',obj.company_id.id), ('amount_residual','!=', 0), ('account_id.internal_type', 'in', ('receivable','payable'))])
            whole_old_invoices = acc_move_obj.search([('date_maturity','<=',  start_date), ('move_id.state', '=', 'posted'), ('move_id.company_id','=',obj.company_id.id), ('amount_residual','!=', 0), ('account_id.internal_type', 'in', ('receivable','payable'))])
            forecasted_invoices = forecast_obj.search([('date_invoice','>',  start_date), ('date_invoice','<=', end_date), ('amount','!=', 0)])
            forecasted_old_invoices = forecast_obj.search([('date_invoice','<=',  start_date), ('amount','!=', 0)])
            customers = (whole_invoices + whole_old_invoices).mapped('move_id.partner_id')
            customers = customers.mapped(lambda p: p.parent_id or p)
            customers = customers.sorted('name')
            
            customers_forecasted = (forecasted_invoices + forecasted_old_invoices).mapped('sale_id.partner_id')
            customers_forecasted = customers_forecasted.sorted('name')
            customer_included = customers + customers_forecasted
            customer_included = sorted(set(customer_included))
            # sale_ids = 
            print (customers_forecasted)
            print (customers)
            print (customer_included)
            
            

            # total_forecates = 0
            # for forecasted in forecasted_invoices:
            #     whole_partner_id = whole.partner_id.id
            #     whole_date_maturity = whole.date_maturity
            #     sale_order_id = []
            #     for sale_line in whole.sale_line_ids:
            #         sale_order_id.append(sale_line.order_id.id)
            #     # sale_order_id = whole.sale_line_ids[0].order_id.id
            #     sale_order_map = whole._sale_determine_order()
            #     sale_order = sale_order_map.get(whole.id)
            #     print (sale_order_id, 'ffffg')
            #     if sale_order:
            #         print (sale_order, 'ffffg')
            #         v
            # ff1






            sheet.write(0,0, obj.company_id.name + ' - Cash Flow Forecast', title_header)
            sheet.write(1,0, "Amounts (" + obj.company_id.currency_id.name + ")")

            row = 2
            column = 2

            for index, month in enumerate(months):
                length = len(month)-1
                sheet.merge_range(row, column, row, column+length, month[0].strftime("%b-%d"), table_header)
                for i, week in enumerate(month):
                    sheet.write(row+1, column+i, week.strftime("%d.%m.%Y"), table_header)
                    sheet.write(row+2, column+i, "", table_header)
                    sheet.write(row+3, column+i, index == 0 and i == 0 and "ACT" or "ETC", table_header)
                column += length
                column += 1
            row += 6

            sheet.merge_range(row-6, 1, row-3, 1, "Previous Outstanding", table_header)

            sheet.set_column(1, column, 20)

            sheet.write(row, 0, "Cash Received:", bold)
            row += 1
            for partner in customer_included:
                invoices = whole_invoices.filtered(lambda x: x.move_id.partner_id.id == partner.id)
                

                invoice_forecasted = forecasted_invoices.filtered(lambda x: x.sale_id.partner_id.id == partner.id)
                sheet.write(row, 0, partner.name)
                column = 2
                old_unpaid_invoice = whole_old_invoices.filtered(lambda x: x.partner_id.id == partner.id)

                old_forecasted_unpaid_invoice = forecasted_old_invoices.filtered(lambda x: x.sale_id.partner_id.id == partner.id)
                if not old_unpaid_invoice:
                    old_unpaid_invoice = whole_old_invoices.filtered(lambda x: x.partner_id.id in partner.child_ids.ids)
                    old_forecasted_unpaid_invoice = forecasted_old_invoices.filtered(lambda x: x.sale_id.partner_id.id in partner.child_ids.ids)
                residual_old_invoice = sum(old_unpaid_invoice.mapped('amount_residual'))
                residual_old_forecasted_unpaid_invoice = sum(old_forecasted_unpaid_invoice.mapped('amount'))
                
                residual_old = residual_old_invoice + residual_old_forecasted_unpaid_invoice
                sheet.write(row, column-1, residual_old, table_content)
                for index, month in enumerate(months):               
                    length = len(month)-1
                    for i, week in enumerate(month):
                        week_start = week + timedelta(days= -7)
                        # receivable = sum(invoices.filtered(lambda x: x.move_id.move_type in ('out_invoice', 'in_refund') and x.date_maturity <= week and x.date_maturity > week_start).mapped('debit'))
                        # payable = sum(invoices.filtered(lambda x: x.move_id.move_type in ('in_invoice', 'out_refund') and x.date_maturity <= week and x.date_maturity > week_start).mapped('credit'))
                        # residual = sum(invoices.filtered(lambda x: x.move_id.move_type in ('in_invoice', 'out_refund') and x.date_maturity <= week and x.date_maturity > week_start).mapped('amount_residual'))
                        residual_invoice = sum(invoices.filtered(lambda x:  x.date_maturity <= week and x.date_maturity > week_start).mapped('amount_residual'))
                        residual_forecasted = sum(invoice_forecasted.filtered(lambda x:  x.date_invoice <= week and x.date_invoice > week_start).mapped('amount'))
                        residual = residual_forecasted + residual_invoice
                        if i == 0:
                            # sheet.write(row, column+i, receivable-payable, left_border)
                            sheet.write(row, column+i, residual, left_border)
                        elif i == length:
                            # sheet.write(row, column+i, receivable-payable, right_border)
                            sheet.write(row, column+i, residual, right_border)
                        else:
                            # sheet.write(row, column+i, receivable-payable, table_content)
                            sheet.write(row, column+i, residual, table_content)
                    column += length
                    column += 1
                row += 1
