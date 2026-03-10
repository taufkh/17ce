# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockMove(models.Model):
	_inherit = "stock.move"

	def _get_source_document(self):
		res = super()._get_source_document()
		context = dict(self._context or {})
		if context.get('from_icon_replenishment'):
			return self.sale_line_id or res
		return self.sale_line_id.order_id or res

	# def action_assign_serial_show_details(self):
	# 	""" On `self.move_line_ids`, assign `lot_name` according to
	# 	`self.next_serial` before returning `self.action_show_details`.
	# 	"""
	# 	self.ensure_one()
	# 	if not self.next_serial:
	# 		raise UserError(_("You need to set a Serial Number before generating more."))
	# 	self._generate_serial_numbers()
	# 	return self.action_show_details()

	# def action_assign_serial(self):
	# 	""" Opens a wizard to assign SN's name on each move lines.
	# 	"""
	# 	self.ensure_one()
	# 	action = self.env["ir.actions.actions"]._for_xml_id("stock.act_assign_serial_numbers")
	# 	action['context'] = {
	# 		'default_product_id': self.product_id.id,
	# 		'default_move_id': self.id,
	# 	}
	# 	return action