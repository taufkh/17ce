# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Jesni Banu(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
# import datetime
# from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
import datetime
from datetime import datetime, timedelta
import pytz
from odoo import models,api, SUPERUSER_ID
from dateutil import parser
from dateutil.relativedelta import relativedelta
import operator
# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


class IconSalesReport(models.AbstractModel):
	_name = 'report.iconnexion_custom.icon_salesreport'
	_description = 'iConnexion Sales XLSX Report'
	_inherit = 'report.report_xlsx.abstract'

	def generate_xlsx_report(self, workbook, data, partners):
		sheet = workbook.add_worksheet("Report")
		for i, obj in enumerate(partners):
			bold = workbook.add_format({"bold": True})
			sheet.write(i, 0, obj.name, bold)
# IconSalesReport('report.res.partner.xlsx', 
#             'res.partner')
	# def get_warehouse(self, data):
	# 	l1 = []
	# 	l2 = []
	# 	l3 = []
	# 	l4 = []		
	# 	if data.get('form', False) and data['form'].get('warehouse_ids', False):			
	# 		obj = self.env['stock.warehouse'].search([('id', 'in', data['form']['warehouse_ids'])])
	# 		for j in obj:
	# 			l1.append(j.name)
	# 			l2.append(j.id)
	# 	else:
	# 		obj = self.env['stock.warehouse'].search([])#,order='report_sequence asc')			
	# 		for j in obj:
	# 			l1.append(j.name)
	# 			l2.append(j.id)
	# 	return l1, l2, l3 , l4

	# def get_product(self, data):
	# 	product_ids = []
	# 	query = "SELECT ID FROM PRODUCT_PRODUCT WHERE ACTIVE = TRUE "
	# 	all_data = True
	# 	if data.get('form', False) and data['form'].get('grouping_ids', False):			
	# 		l1 = data['form']['grouping_ids']
	# 		all_data = False
	# 		if len(l1) == 1:
	# 			query += " and group_1_id = %s " % l1[0]
	# 		else:
	# 			query += " and group_1_id in "
	# 			query += ( str( tuple(l1) ) ) 

	# 	if data.get('form', False) and data['form'].get('grouping2_ids', False):
	# 		l2 = data['form']['grouping2_ids']
	# 		all_data = False
	# 		if len(l2) == 1:
	# 			query += " and group_2_id = %s " % l2[0]
	# 		else:
	# 			query += " and group_2_id in "
	# 			query += ( str( tuple(l2) ) ) 
	# 	if data.get('form', False) and data['form'].get('grouping3_ids', False):
	# 		l3 = data['form']['grouping3_ids']
	# 		all_data = False
	# 		if len(l3) == 1:
	# 			query += " and group_3_id = %s " % l3[0]
	# 		else:
	# 			query += " and group_3_id in "
	# 			query += ( str( tuple(l3) ) ) 

	# 	if data.get('form', False) and data['form'].get('item_ids', False):
	# 		l4 = data['form']['item_ids']
	# 		all_data = False
	# 		if len(l4) == 1:
	# 			query += " and id = %s " % l4[0]
	# 		else:
	# 			query += " and id in "
	# 			query += ( str( tuple(l4) ) ) 
		
	# 	# if group
	# 	# estmasi minggu ini bakal disesleikan, kita bakal testing internal dulu .
		
	# 	if all_data:
	# 		self.env.cr.execute("""
	# 			SELECT ID FROM PRODUCT_PRODUCT WHERE ACTIVE = TRUE
	# 			""")
	# 		res_query = self.env.cr.fetchall()
	# 		product_ids = [b[0] for b in res_query]
	# 		return product_ids
	# 	else:
	# 		self.env.cr.execute(query)
	# 		res_query = self.env.cr.fetchall()
	# 		product_ids = [b[0] for b in res_query]

	# 	return product_ids
	

	# def get_lines(self, data, warehouse,product_ids):
	# 	lines = []
	# 	#find transaction last month
	# 	session_obj = self.env['pos.session']
	# 	warehouse_obj = self.env['stock.warehouse']
	# 	# date_end = datetime.strptime(data['form']['end_date'],"%Y-%m-%d")
	# 	# date_starts = str(data['form']['end_date'])[:4]
	# 	# date_stops = datetime.strptime(data['form']['end_date'],"%Y-%m-%d") + relativedelta(months=-1)
	# 	# date_start = datetime.strptime(date_starts+"-01-01","%Y-%m-%d")
	# 	# #From Date Looping by Month
	# 	# start_date = data['form']['start_date'] + ' 00:00:00'
	# 	# end_date = data['form']['end_date'] + ' 23:59:59'
	# 	# date_start = datetime.strptime(data['form']['start_date'],'%Y-%m-%d')
	# 	# date_start = date_start.strftime('%d-%m-%Y')
	# 	# date_end = datetime.strptime(data['form']['end_date'],'%Y-%m-%d')
	# 	# date_end = date_end.strftime('%d-%m-%Y')
	# 	start_date = data['form']['start_date']# + ' 00:00:00'
	# 	end_date = data['form']['end_date'] #+ ' 23:59:59'
	# 	location_id = warehouse_obj.browse(warehouse).lot_stock_id.id

	# 	self.env.cr.execute("""
	# 		SELECT pp.active, pp.barcode, pt.name, pu.name AS uom,
	# 			(SELECT SUM(product_qty) FROM stock_move
	# 			WHERE date < %s AND location_dest_id = %s AND state = 'done' AND product_id = pp.id) AS start_stock_in,
	# 			(SELECT SUM(product_qty) FROM stock_move
	# 			WHERE date < %s AND location_id = %s AND state = 'done' AND product_id = pp.id) AS start_stock_out,
	# 			(SELECT SUM(product_qty) FROM stock_move
	# 			WHERE date >= %s AND date <= %s AND location_dest_id = %s AND state = 'done' AND product_id = pp.id) AS in_stock,
	# 			(SELECT SUM(product_qty) FROM stock_move
	# 			WHERE date >= %s AND date <= %s AND location_id = %s AND state = 'done' AND product_id = pp.id) AS out_stock,
	# 			(SELECT value_float FROM ir_property
	# 			WHERE name IN ('standard_price','standard price') AND res_id = CONCAT('product.product,',pp.id)) AS cost
	# 			FROM product_template pt 
	# 		INNER JOIN product_product pp ON pp.product_tmpl_id = pt.id
	# 		INNER JOIN uom_uom pu ON pu.id = pt.uom_id where pp.active = True and pt.active = True and pp.id in %s 
	# 	""",(start_date, location_id, start_date, location_id, start_date, end_date, location_id, start_date, end_date, location_id,tuple(product_ids) ))
	# 	res_query = self.env.cr.fetchall()
	# 	fmt = '{:,.2f}'.format
	# 	total_start_cost = 0
	# 	total_end_cost = 0
	# 	total_in_stock = 0
	# 	total_out_stock = 0
	# 	total_start_stock = 0
	# 	total_in_stock_cost = 0
	# 	total_out_stock_cost = 0
		

	# 	for active,kode,nama_barang,uom,start_stock_in,start_stock_out,in_stock,out_stock,cost in res_query:
	# 		# print 'testttttt'
	# 		# total_cost = 0
	# 		if active == False:
	# 			continue
	# 		start_stock = ((start_stock_in or 0)-(start_stock_out or 0)) or 0
	# 		in_stock = in_stock or 0
	# 		out_stock = out_stock or 0
	# 		cost = cost or 0
	# 		total_cost =((start_stock+in_stock-out_stock)*cost)
	# 		vals ={
	# 			'kode': kode,
	# 			'nama_barang':nama_barang,
	# 			'nilai': total_cost,
	# 			'start_stock' : start_stock,
	# 			'start_stock_in' :start_stock_in,
	# 			'start_stock_out' :start_stock_out,
	# 			'in_stock' :in_stock,
	# 			'out_stock' :out_stock,
	# 			'cost' : cost,
	# 			'uom': uom,
	# 		}


	# 		lines.append(vals)
	# 		# date_start += relativedelta(months=1)
		
	# 	return lines
	
	# def generate_xlsx_report(self, workbook, data, lines):
	# 	#Setting date
	# 	print ('sukser123123123123'*5)
	# 	date_start = datetime.strptime(data['form']['start_date'],'%Y-%m-%d %H:%M:%S')
	# 	date_start = date_start.strftime('%d-%m-%Y')

	# 	date_end = datetime.strptime(data['form']['end_date'],'%Y-%m-%d %H:%M:%S')
	# 	date_end = date_end.strftime('%d-%m-%Y')

		
	# 	date_transaction = datetime.strptime(data['form']['start_date'],"%Y-%m-%d %H:%M:%S") + relativedelta(hours =+7)
	# 	date_start = date_transaction.strftime('%d-%m-%Y %H:%M:%S')
		
		
	# 	date_transaction = datetime.strptime(data['form']['end_date'],"%Y-%m-%d %H:%M:%S") + relativedelta(hours =+7)
	# 	date_end = date_transaction.strftime('%d-%m-%Y %H:%M:%S')
	# 	date_ends = date_transaction.strftime('%Y')

	# 	# date_starts = str(data['form']['date_end'])[:4]
	# 	fmt = '{:,.2f}'.format
	# 	# get_warehouse = self.get_warehouse(data)
	# 	# get_product = self.get_product(data)
	# 	# # print ('sdfadaaaaaaaaaaaaaaaaaa',get_product)
	# 	# # [0] = group 1 , [1] = group 2 

	# 	# count = len(get_warehouse[0]) * 11 + 6
	# 	sheet = workbook.add_worksheet('Lap Stock Gudang '+ str(date_ends) )
	# 	format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
	# 	format1a = workbook.add_format({'font_size': 10, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
	# 	format1b = workbook.add_format({'font_size': 10, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': False})
	# 	format1bc = workbook.add_format({'font_size': 10, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': False, 'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
	# 	format1bb = workbook.add_format({'font_size': 10, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
	# 	format1bb2 = workbook.add_format({'font_size': 10, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center', 'bold': True})
	# 	format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
	# 	format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
	# 	format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
	# 	font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8, 'num_format':'#,##0'})
	# 	red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,
	# 									'bg_color': 'red'})
	# 	justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
	# 	White_mark = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True, 'bg_color': 'white'} )
	# 	Green_mark = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True, 'bg_color': 'green'} )
	# 	Purple_mark = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True, 'bg_color': 'purple'} )
	# 	Blue_mark = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True, 'bg_color': 'blue'} )
	# 	Pink_mark = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True, 'bg_color': 'pink'} )
	# 	Grey_mark = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True, 'bg_color': '#808080'} )
	# 	Yellow_mark	= workbook.add_format({'font_size': 7, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True, 'bg_color': 'yellow', 'num_format':'#,##0'} )	
	# 	Normal_mark	= workbook.add_format({'font_size': 7, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True, 'bg_color': 'white', 'num_format':'#,##0'} )	
	# 	format3.set_align('center')
	# 	font_size_8.set_align('center')
	# 	justify.set_align('justify')
	# 	format1.set_align('center')
	# 	red_mark.set_align('center')
	# 	sheet.fit_width_to_pages = 1

	# 	#extra formatting
	# 	title = workbook.add_format({'font_size': 16, 'align': 'vcenter', 'bold': True })
	# 	subtitle = workbook.add_format({'font_size': 13, 'bottom': True, 'align': 'vcenter', 'italic': True})
	# 	headertop = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'bold': True})
	# 	headerbottom = workbook.add_format({'font_size': 10,'align': 'vcenter', 'bold': False})
	# 	content = workbook.add_format({'font_size': 10, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'right', 'bold': False})
	# 	grandtotal = workbook.add_format({'font_size': 10, 'top': True, 'bottom': True, 'left': True, 'right': True, 'align': 'center'})
	# 	footertotal = workbook.add_format({'font_size': 10, 'top': True, 'bottom': True, 'left': True, 'right': True, 'align': 'center', 'bold': True})

	# 	users = self.env['res.users'].browse(SUPERUSER_ID)
	# 	sheet.merge_range('A1:G1', ''+ str(self.env.company.name), title)
	# 	sheet.merge_range('A2:J2', 'Laporan Sisa Stock', subtitle)
	# 	sheet.merge_range('A3:B3', 'Warehouse :', headertop)
	# 	# sheet.merge_range('A4:B4', str(get_warehouse[0])[3:-2], headerbottom)
	# 	sheet.merge_range('D3:E3', 'Start Date :', headertop)
	# 	sheet.merge_range('D4:E4', date_start, headerbottom)
	# 	sheet.merge_range('G3:H3', 'End Date :', headertop)
	# 	sheet.merge_range('G4:H4', date_end, headerbottom)
	# 	sheet.write('J3', 'Print Date :', headertop)

	# 	now = datetime.now()+timedelta(hours=7)
	# 	sheet.write('J4:K4',now.strftime('%Y-%m-%d %H:%M:%S'), headerbottom)

	# 	sheet.write('A6', 'NO', format1bb)
	# 	sheet.write('B6', 'KODE', format1bb)
	# 	sheet.write('C6', 'NAMA BARANG', format1bb)
	# 	sheet.set_column('B5:B5', 16.46)
	# 	sheet.set_column('C5:C5', 35.46)
	# 	sheet.write('D6', 'SISA (OH)', format1bb)
	# 	# sheet.write('D6', 'AWAL (AC)', format1bb)
	# 	# sheet.set_column('C5:C5', 20.96)
	# 	# sheet.write('E6', '@', format1bb)
	# 	sheet.set_column('D5:D5', 10.30)
	# 	# sheet.write('F6', 'AWAL NILAI', format1bb)
	# 	sheet.set_column('F5:F5', 10.96)
	# 	# sheet.write('G6', 'MASUK', format1bb)
	# 	# sheet.write('H6', 'KELUAR', format1bb)
	# 	# sheet.write('I6', 'SISA (AC)', format1bb)
	# 	# sheet.write('J6', '@', format1bb)
	# 	sheet.set_column('J5:J5', 10.30)
	# 	# sheet.write('K6', 'NILAI', format1bb)
	# 	sheet.set_column('L5:L5', 11.20)
		
	# 	#totals variable
	# 	total_start_stock = 0
	# 	total_in_stock = 0
	# 	total_out_stock = 0
	# 	total_in_stock_cost = 0
	# 	total_out_stock_cost = 0
	# 	total_start_cost = 0
	# 	total_end_cost = 0

	# 	w_col_no = 1
	# 	w_col_no1 = 2
	# 	x = 0
	# 	color_dict = {}
	# 	color_dict_10_b = {}
	# 	color_dict_10 = {}
	# 	color_dict_8 = {}
	# 	# for i in get_warehouse[0]:
	# 	# 	# print 'get_warehouse',i
	# 	# 	x += 1
			
	# 	# n = 0
	# 	# for i in get_warehouse[0]: #Header 1
	# 	# 	n += 1	
	# 	# 	w_col_no = w_col_no + 1
	# 	# 	# sheet.merge_range(3, w_col_no1 , 3, w_col_no, i, format1b)
	# 	# 	# sheet.merge_range(4, w_col_no1+1,4, w_col_no1+ , i, format1b)
	# 	# 	sheet.write(5, w_col_no1+1 , i, format1bb)			
	# 	# 	w_col_no1 = w_col_no1 +1

	# 	# sheet.merge_range(3, 3 , 3, w_col_no1 +1 , 'Nilai Stock', format1bb2)
	# 	sheet.write(5, w_col_no1+1 , 'Total', format1bb)
	# 	sheet.write(5, w_col_no1+2 , 'Unit Satuan', format1bb)
	# 	# sheet.set_column(w_col_no1,w_col_no1, 24.46)
		



	# 	prod_row = 6
	# 	prod_col = 3
	# 	nd = 0
	# 	total_value = {}
	# 	total_oh = {}
	# 	print ('aukseeeeeeeeeeeeeeeeeeeeeeee123123'*3)
		# for i in get_warehouse[1]:			
		# 	#Untuk cari transaksi bulan sebelum nya looping perbulan,
		# 	nd += 1
		# 	no = 1
		# 	get_line = self.get_lines(data, i,get_product)
		# 	for each in get_line:
		# 		if prod_row in total_value:
		# 			total_value[prod_row] += each['nilai']
		# 			total_oh[prod_row] += each['start_stock']+each['in_stock']-each['out_stock']
		# 		else:
		# 			total_value[prod_row] = each['nilai']
		# 			total_oh[prod_row] = each['start_stock']+each['in_stock']-each['out_stock']

		# 		sheet.write(prod_row , 0, no, content)
		# 		sheet.write(prod_row , 1, each['kode'], format1b)
		# 		sheet.write(prod_row , 2, each['nama_barang'], format1b)
		# 		# sheet.write(prod_row , 3, (total_oh[prod_row]) and str(int(total_oh[prod_row]))+' '+each['uom'] or '', content)
		# 		# sheet.write(prod_row, 3, each['start_stock'] and str(int(each['start_stock']))+ ' ' + each['uom'] or '', content)
		# 		# sheet.write(prod_row, 4, each['start_stock'] and each['cost'] and fmt(each['cost']) or '-', content)
		# 		# sheet.write(prod_row, 5, each['start_stock'] and each['cost'] and (each['start_stock']*each['cost']) and fmt(each['start_stock']*each['cost']) or '-', content)
		# 		# sheet.write(prod_row, 6, each['in_stock'] and str(int(each['in_stock'])) + ' ' + each['uom'] or ' ', content)
		# 		# sheet.write(prod_row, 7, each['out_stock'] and str(int(each['out_stock']))+' '+each['uom'] or ' ', content)
		# 		# sheet.write(prod_row, 8, (each['start_stock']+each['in_stock']-each['out_stock']) and str(int(each['start_stock']+each['in_stock']-each['out_stock']))+' '+each['uom'] or '', content)
		# 		# sheet.write(prod_row, 9, (each['start_stock']+each['in_stock']-each['out_stock']) and each['cost'] and fmt(each['cost']) or '-', content)
		# 		# sheet.write(prod_row, 10, (each['start_stock']+each['in_stock']-each['out_stock'])*each['cost'] and fmt(((each['start_stock']+each['in_stock']-each['out_stock'])*each['cost'])) or '-', content)
			
		# 		deach = each['start_stock']+each['in_stock']-each['out_stock']
		# 		if total_oh[prod_row]:
		# 			dtotal_oh = total_oh[prod_row]
		# 		else:
		# 			dtotal_oh = 0
   
		# 		if deach == 0:
		# 			deach = 0
		# 		if dtotal_oh == 0:
		# 			dtotal_oh = 0
   
		# 		sheet.write(prod_row, prod_col + 0, deach, format1bc)
				
		# 		# sheet.write(prod_row, prod_col + 8, "{:,}".format(total_value[prod_row]), Yellow_mark)
		# 		if total_oh[prod_row]:
		# 			sheet.write(prod_row, prod_col + 1, dtotal_oh, format1bc)
		# 		else:
		# 			sheet.write(prod_row, prod_col + 1, 0, format1bc)

		# 		sheet.write(prod_row, prod_col + 2, each['uom'] or '', format1b)

		# 		total_start_stock += each['start_stock']
		# 		total_in_stock += each['in_stock']
		# 		total_out_stock += each["out_stock"]
		# 		total_in_stock_cost +=each['in_stock'] * each['cost']
		# 		total_out_stock_cost +=each['out_stock'] * each['cost']
				
		# 		total_start_cost+=each['start_stock'] and each['cost'] and (each['start_stock']*each['cost'])
		# 		total_end_cost+=((each['start_stock']+each['in_stock']-each['out_stock'])*each['cost'])
		# 		#
		# 		no = no + 1
		# 		prod_row = prod_row + 1
		# 		prod_rows = prod_row

			
			# break

			#writing footer part of the reports
			# prod_row += 1
			# mergerange = "A%s:C%s" %(prod_row, prod_row)
			# sheet.merge_range(mergerange, 'GRAND TOTAL', grandtotal)
			# sheet.write(prod_row-1, 3, 'IDR', grandtotal)
			# sheet.write(prod_row-1, 9, fmt(total_end_cost), content)

			# #---------------------------------------------------
			# prod_row += 2
			# mergerange = "B%s:C%s" %(prod_row, prod_row)
			# sheet.merge_range(mergerange, 'Total Qty Awal', footertotal)
			# sheet.write(prod_row-1, 3, ' ', footertotal)
			# mergerange = "E%s:F%s" %(prod_row, prod_row)
			# sheet.merge_range(mergerange, fmt(total_start_stock), content)

			# prod_row += 1
			# mergerange = "B%s:C%s" %(prod_row, prod_row)
			# sheet.merge_range(mergerange, 'Total Qty Masuk', footertotal)
			# sheet.write(prod_row-1, 3, ' ', footertotal)
			# mergerange = "E%s:F%s" %(prod_row, prod_row)
			# sheet.merge_range(mergerange, fmt(total_in_stock), content)

			# prod_row += 1
			# mergerange = "B%s:C%s" %(prod_row, prod_row)
			# sheet.merge_range(mergerange, 'Total Qty Keluar', footertotal)
			# sheet.write(prod_row-1, 3, '', footertotal)
			# mergerange = "E%s:F%s" %(prod_row, prod_row)
			# sheet.merge_range(mergerange, fmt(total_out_stock), content)

			# prod_row += 1
			# mergerange = "B%s:C%s" %(prod_row, prod_row)
			# sheet.merge_range(mergerange, 'Grand Total Inventory Awal', footertotal)
			# sheet.write(prod_row-1, 3, str(users.company_id.currency_id.name), footertotal)
			# mergerange = "E%s:F%s" %(prod_row, prod_row)
			# sheet.merge_range(mergerange, fmt(total_start_cost), content)

			# prod_row += 1
			# mergerange = "B%s:C%s" %(prod_row, prod_row)
			# sheet.merge_range(mergerange, 'Total Inventory Masuk', footertotal)
			# sheet.write(prod_row-1, 3, str(users.company_id.currency_id.name), footertotal)
			# mergerange = "E%s:F%s" %(prod_row, prod_row)
			# sheet.merge_range(mergerange, fmt(total_in_stock_cost), content)

			# prod_row += 1
			# mergerange = "B%s:C%s" %(prod_row, prod_row)
			# sheet.merge_range(mergerange, 'Total Inventory Keluar', footertotal)
			# sheet.write(prod_row-1, 3, str(users.company_id.currency_id.name), footertotal)
			# mergerange = "E%s:F%s" %(prod_row, prod_row)
			# sheet.merge_range(mergerange, fmt(total_out_stock_cost), content)

			# prod_row += 1
			# mergerange = "B%s:C%s" %(prod_row, prod_row)
			# sheet.merge_range(mergerange, 'Grand Total Inventory Akhir', footertotal)
			# sheet.write(prod_row-1, 3, str(users.company_id.currency_id.name), footertotal)
			# mergerange = "E%s:F%s" %(prod_row, prod_row)
			# sheet.merge_range(mergerange, fmt(total_end_cost), content)

			# prod_col = prod_col + 1
			# prod_row = 6

			

		# 	prod_row = prod_row_total
		# 	# break

		# prod_col = 2
		# nd = 0
		# total_omset2 = {}
		# Grand_total_omset = 0.0
		# for i in get_warehouse[1]: #get total transaction this month
		# 	#Untuk cari transaksi total bulan ini,
		# 	is_split = get_warehouse[3][nd]
		# 	grand_total = self.get_grand_total(data, i)
		# 	Grand_total_omset += grand_total['omset_float']
		# 	nd += 1
		# 	if not is_split:
		# 		sheet.merge_range(prod_row + 1, 0 + 0, prod_row +1 , 1, 'Grand Total', format11)
		# 		sheet.write(prod_row + 1, prod_col + 6, 'Grand Total', format11)
		# 		# sheet.write_formula(prod_row + 1,prod_col + 7,'=SUM('7'' )
		# 		sheet.write(prod_row + 1, prod_col + 7, grand_total['omset'], Normal_mark)
		# 		 # omset_float
		# 		prod_col = prod_col + 8
		# 	if is_split:
		# 		sheet.merge_range(prod_row + 1, 0 + 0, prod_row +1 , 1, 'Grand Total', format11)
		# 		sheet.write(prod_row + 1, prod_col + 8, 'Grand Total', format11)
		# 		# sheet.write_formula(prod_row + 1,prod_col + 7,'=SUM('7'' )
		# 		sheet.write(prod_row + 1, prod_col + 9, grand_total['omset'], Normal_mark)
		# 		# sheet.write(prod_row + 1, prod_col + 10, Grand_total_omset, Normal_mark)
		# 		prod_col = prod_col + 10
		# sheet.write(prod_row + 1, prod_col + 0, Grand_total_omset, Normal_mark)

