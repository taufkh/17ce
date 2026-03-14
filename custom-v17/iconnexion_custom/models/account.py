# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
	_inherit = 'account.move'

	contact_id = fields.Many2one("res.partner", "Contacts", compute='_compute_sale_order')
	customer_ref = fields.Char('Customer No Ref',)
	sale_quotation_no_id = fields.Many2one('sale.order', 'Sale Quotation No', compute='_compute_sale_order')
	sale_order_no_id = fields.Many2one('sale.order', 'Sale Order No (Derived)', compute='_compute_sale_order')
	po_no = fields.Char('PO No',compute='_compute_sale_order')
	is_iconnexion = fields.Boolean(string="iConnexion Company", compute='compute_is_iconnexion', store=True)
	invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, index=True, default=fields.Datetime.now, copy=False)

	@api.constrains('ref', 'move_type', 'partner_id', 'journal_id', 'invoice_date')
	def _check_duplicate_supplier_reference(self):
		moves = self.filtered(lambda move: move.is_purchase_document() and move.ref)
		if not moves:
			return

		self.env["account.move"].flush([
			"ref", "move_type", "invoice_date", "journal_id",
			"company_id", "partner_id", "commercial_partner_id",
		])
		self.env["account.journal"].flush(["company_id"])
		self.env["res.partner"].flush(["commercial_partner_id"])

		# /!\ Computed stored fields are not yet inside the database.
		self._cr.execute('''
			SELECT move2.id
			FROM account_move move
			JOIN account_journal journal ON journal.id = move.journal_id
			JOIN res_partner partner ON partner.id = move.partner_id
			INNER JOIN account_move move2 ON
				move2.ref = move.ref
				AND move2.company_id = journal.company_id
				AND move2.commercial_partner_id = partner.commercial_partner_id
				AND move2.move_type = move.move_type
				AND (move.invoice_date is NULL OR move2.invoice_date = move.invoice_date)
				AND move2.id != move.id
			WHERE move.id IN %s
		''', [tuple(moves.ids)])
		duplicated_moves = self.browse([r[0] for r in self._cr.fetchall()])
		#if duplicated_moves:
		#	raise ValidationError(_('Duplicated vendor reference detected. You probably encoded twice the same vendor bill/credit note:\n%s') % "\n".join(
		#		duplicated_moves.mapped(lambda m: "%(partner)s - %(ref)s - %(date)s" % {'ref': m.ref, 'partner': m.partner_id.display_name, 'date': format_date(self.env, m.date)})
		#	))

	@api.model_create_multi
	def create(self, vals_list):
		context = dict(self._context or {})
		sale_id = None
		# for_from sales

		if context.get('sale_order_id'):
			sale_id = self.env['sale.order'].browse(context.get('sale_order_id'))

		if sale_id:
			inv_name = sale_id.name.replace(self.env.company.quotation_new_prefix, 'INV')
			for vals in vals_list:
				vals['name'] = f"{inv_name}-{len(sale_id.invoice_ids) + 1}"

		return super().create(vals_list)

	@api.depends('company_id')
	def compute_is_iconnexion(self):
		for account in self:
			company_name = account.company_id.name
			if company_name and 'iconnexion' in company_name.lower():
				account.is_iconnexion = True
			else:
				account.is_iconnexion = False

	# @api.depends('invoice_line_ids')
	def _compute_sale_order(self):
		for account in self:
			account.sale_quotation_no_id = False
			account.sale_order_no_id = False
			account.po_no = False
			account.contact_id = False
			sale_line_id = False
			for line in account.invoice_line_ids:
				for sale in line.sale_line_ids: #for get sale order
					sale_line_id = sale
					break
				if sale_line_id:
					break
			if sale_line_id:
				# quotation_sale_id
				account.sale_order_no_id = sale_line_id.order_id.id
				if sale_line_id.order_id.quotation_sale_id:
					account.sale_quotation_no_id = sale_line_id.order_id.quotation_sale_id.id
				account.po_no = sale_line_id.order_id.client_order_ref
				if sale_line_id.order_id:
					account.contact_id = sale_line_id.order_id.contact_id.id

	def button_send_notif(self):
		for move in self:
			if move.invoice_payment_term_id:
				partner_ids = []
				for cs in self.company_id.icon_customer_service_ids:
					partner_ids.append(cs.id)
				if partner_ids:
					if 'tt' in move.invoice_payment_term_id.name.lower():
						 move.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
								'iconnexion_custom.finance_confirm_payment_template',
							values={'invoice': move,},
							subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
							partner_ids=partner_ids,
							subject='Finance Received a TT-in-advance payment order '+ move.name,                            
					) 
		return True


	def action_post(self):
		invoice = super(AccountMove, self).action_post()
		for account in self:
			account._check_balanced_icon()
	# 		if account.invoice_payment_term_id:
	# 			if 'tt' in account.invoice_payment_term_id.name.lower():
	# 				partner_ids = []
	# 				for cs in self.company_id.icon_customer_service_ids:
	# 					partner_ids.append(cs.id)
	# 				for finance in self.company_id.icon_finance_ids:
	# 					partner_ids.append(finance.id)
	# 				if partner_ids:
	# 					account.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
	# 						'iconnexion_custom.cs_finance_update_template',
	# 						values={'invoice': account,},
	# 						subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
	# 						partner_ids=partner_ids,notify = False,
	# 						subject='Salesman confirms a TT-in-advance payment order '+ account.name,                            
	# 					)
	# 		# if account.ref:
	# 		# 	self.customer_ref = account.ref				
				

		return invoice

	def _check_balanced_icon(self):
		''' Assert the move is fully balanced debit = credit.
		An error is raised if it's not the case.
		'''
		moves = self.filtered(lambda move: move.line_ids)
		if not moves:
			return

		# /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
		# are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
		# It happens as the ORM makes the create with the 'no_recompute' statement.
		self.env['account.move.line'].flush(self.env['account.move.line']._fields)
		self.env['account.move'].flush(['journal_id'])
		self._cr.execute('''
			SELECT line.move_id, ROUND(SUM(line.debit - line.credit), currency.decimal_places)
			FROM account_move_line line
			JOIN account_move move ON move.id = line.move_id
			JOIN account_journal journal ON journal.id = move.journal_id
			JOIN res_company company ON company.id = journal.company_id
			JOIN res_currency currency ON currency.id = company.currency_id
			WHERE line.move_id IN %s
			GROUP BY line.move_id, currency.decimal_places
			HAVING ROUND(SUM(line.debit - line.credit), currency.decimal_places) != 0.0;
		''', [tuple(self.ids)])

		query_res = self._cr.fetchall()
		if query_res:
			
			ids = [res[0] for res in query_res]
			sums = [res[1] for res in query_res]
			raise UserError(_("Cannot create unbalanced journal entry. Ids: %s\nDifferences debit - credit: %s. Please recompute journal or balance it by adjust debit - creditt") % (ids, sums))




class AccountPayment(models.Model):
	_inherit = 'account.payment'

	sale_id = fields.Many2one('sale.order', 'Sale Order')
