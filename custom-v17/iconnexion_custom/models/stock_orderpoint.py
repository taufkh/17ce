from odoo import SUPERUSER_ID, _, api, fields, models, registry

class StockWarehouseOrderpoint(models.Model):
	_inherit = "stock.warehouse.orderpoint"

	@api.model
	def _get_orderpoint_values(self, product, location):
		product_obj = self.env['product.product']
		product_rec = product_obj.browse(product)
		res = super(StockWarehouseOrderpoint, self)._get_orderpoint_values(product, location)
		res['qty_multiple'] = product_rec.qty_multiply

		return res

	#add replenish signal to pass on to PO
	def _prepare_procurement_values(self, date=False, group=False):        
		res = super(StockWarehouseOrderpoint, self)._prepare_procurement_values(date=date, group=group)
		# product_moves = self.product_id._product_out_moves()
		# related_so = product_moves.mapped('sale_line_id').mapped('order_id').ids
		# modify from odes_purchase feature
		forecast_lines = self.env['report.stock.report_product_product_replenishment']\
                .with_context(from_icon_replenishment=True)._get_report_lines([self.product_tmpl_id.id], [self.product_id.id], [self.location_id.id])
		related_so = []
		related_sl = []
		for forecast in forecast_lines:			
			if forecast['document_out']:
				related_so.append(forecast['document_out'].order_id.id)
				related_sl.append(forecast['document_out'].id)
		
		# res['is_replenish_po'] = True
		if related_so:
			res['related_so'] = [(6, 0, related_so)]
			res['related_sl'] = [(6, 0, related_sl)]
		return res