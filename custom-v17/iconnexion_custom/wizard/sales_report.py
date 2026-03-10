from odoo import api, fields, models, tools, _
from dateutil.relativedelta import relativedelta

import time
import json
import datetime
import io
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter

class IconSalesReportWizard(models.TransientModel):
	_name = "icon.sales.report.wizard"
	_description = "Icon Sales Report Wizard"

	name = fields.Char(string="Name")
	date_start = fields.Date('Start Date', default=fields.Date.today())
	date_end = fields.Date('End Date', default=fields.Date.today())

	# start_date = fields.Datetime(string="Start Date",  default=time.strftime('%Y-%m-01'), required=True)
	# end_date = fields.Datetime(string="End Date",  default=datetime.datetime.now(), required=True)


	# def action_confirm(self):
	# 	self.ensure_one()

	def print_report_xlsx(self):#sisa stock
		context = self._context
		data = {
			'start_date': self.date_start,
			'end_date': self.date_end,
		}
		return {
			'type': 'ir.actions.report',
			'data': {'model': 'icon.sales.report.wizard',
					 'options': json.dumps(data, default=date_utils.json_default),
					 'output_format': 'xlsx',
					 'report_name': 'Sales Report',
					 },
			'report_type': 'xlsx',
		}

	def get_xlsx_report(self, data, response):
		output = io.BytesIO()
		workbook = xlsxwriter.Workbook(output, {'in_memory': True})
		
		sheet = workbook.add_worksheet()
		cell_format = workbook.add_format()
		cell_formatb = workbook.add_format()
		head = workbook.add_format()
		head2 = workbook.add_format()
		head3 = workbook.add_format()
		head4 = workbook.add_format()
		sheet.set_column(0, 0, 10)#A
		sheet.set_column(1, 1, 11)#B
		sheet.set_column(2, 2, 20)#C
		sheet.set_column(3, 3, 60)#D
		sheet.set_column(4, 4, 20)#E
		sheet.set_column(5, 5, 23)#F
		sheet.set_column(6, 6, 18)#G
		sheet.set_column(7, 7, 11)#H
		sheet.set_column(8, 8, 18)#I
		
		
		# txt = workbook.add_format({'font_size': '10px'})
		# date_style = workbook.add_format({'text_wrap': True, 'num_format': 'dd-mm-yyyy'})
		date_style = workbook.add_format()
		number_format = workbook.add_format()
		number_format.set_num_format('#,##0.0000')
		number_format2 = workbook.add_format()
		number_format2.set_num_format('#,##0.')
		# {'num_format': '#,##0.00'}
		date_style.set_num_format('mm/dd/yyyy')
		cell_formatb.set_bold()
		head.set_bold()
		head2.set_bold()
		head3.set_bold()
		head4.set_bold()
		head.set_font_size(13)
		head2.set_font_size(12)
		head3.set_font_size(10)
		head4.set_font_size(8)
		number_format.set_font_size(8)
		number_format2.set_font_size(8)
		head.set_align('center')
		head2.set_align('center')
		head3.set_align('center')

		cell_format.set_font_size(8)
		date_style.set_font_size(8)
		# self.env.cr.execute("""
		# 	SELECT sol.name, sol.product_uom_qty from sale_order_line sol inner join sale_order so
		# 	on so.id = sol.order_id where so.date_order >= %s and so.date_order <= %s
		# 	""", (data['start_date'],data['end_date']) )
		self.env.cr.execute("""
			SELECT am.invoice_date, am.name,am.ref,cs.name,COALESCE(pb.name,''),
			pt.name, P2.name, aml.quantity, aml.price_unit
			 from account_move_line aml inner join account_move am
			on am.id = aml.move_id inner join res_partner cs on cs.id = am.partner_id 
			inner join product_product pp on pp.id = aml.product_id inner join product_template pt on 
			pt.id = pp.product_tmpl_id 
			left join product_brand pb on pb.id = aml.product_id 
			inner join res_users U on am.invoice_user_id = U.id
			inner join res_partner P2 on P2.id = U.partner_id 
			where am.invoice_date >= %s and am.invoice_date <= %s 
			and aml.exclude_from_invoice_tab = False and am.state = 'posted' and am.move_type = 'out_invoice' 
			""", (data['start_date'],data['end_date']) )
		res_query = self.env.cr.fetchall()
		# for query in res_query:
		# 	print ('query',query)
		sheet.merge_range('A1:J2', self.env.company.name, head)
		sheet.merge_range('A4:J4', 'Sales Invoices', head2)
		# sheet.write('B6', 'From:', cell_format)
		
		
		date_temp = datetime.datetime.strptime(data['start_date'],"%Y-%m-%d")				
		date_str = format(date_temp,'%b %d, %Y')
		date_temp2 = datetime.datetime.strptime(data['end_date'],"%Y-%m-%d")	
		date_end = format(date_temp2,'%b %d, %Y')

		sheet.merge_range('A6:J6', date_str +' through '+ date_end,head3)
		# sheet.write('F6', 'To:', cell_format)
		# sheet.merge_range('G6:H6', data['end_date'],txt)

		sheet.write('A9', 'Date', head4)
		sheet.write('B9', 'Doc Num', head4)
		sheet.write('C9', 'P.O. No.', head4)
		sheet.write('D9', 'Customer', head4)
		sheet.write('E9', 'Brand', head4)
		# sheet.write('F9', 'Item Code', cell_formatb)
		sheet.write('F9', 'MPN', head4)
		sheet.write('G9', 'Sales Rep', head4)
		sheet.write('H9', 'Qty', head4)
		sheet.write('I9', 'Price', head4)
		sheet.write('J9', 'Amount', head4)
		
		
		
		
		prod_row = 9
		prod_col = 0
		for q in res_query:
			sheet.write(prod_row , prod_col, q[0], date_style)
			sheet.write(prod_row, 1, q[1], cell_format)
			sheet.write(prod_row, 2, q[2], cell_format)
			sheet.write(prod_row, 3, q[3], cell_format)
			sheet.write(prod_row, 4, q[4], cell_format)
			sheet.write(prod_row, 5, q[5], cell_format)
			sheet.write(prod_row, 6, q[6], cell_format)
			sheet.write(prod_row, 7, q[7], cell_format)
			sheet.write(prod_row, 8, q[8], number_format)
			sheet.write(prod_row, 9, q[7]*q[8], number_format)
			prod_row = prod_row + 1
		sheet.write(prod_row,9, 0, number_format)
		sheet.write_formula(prod_row, 9, '=SUM(J10:J%s)' % (prod_row),number_format ) 
		# mergerange = "B%s:C%s" %(prod_row, prod_row)

		sheet.write(prod_row,8, 'Amount', head4)
		workbook.close()
		output.seek(0)
		response.stream.write(output.read())
		output.close()
# 		datas = {'ids': context.get('active_ids', [])}
# 		datas['model'] = 'icon.sales.report.wizard'
# 		datas['form'] = self.read()[0]
# 		for field in datas['form'].keys():
# 			if isinstance(datas['form'][field], tuple):
# 				datas['form'][field] = datas['form'][field][0]
# #        if context.get('xls_export'):
# 		return self.env.ref('iconnexion_custom.icon_sales_report').report_action(self, data=datas)