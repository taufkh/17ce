# -*- encoding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.parser import parse


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sf_state = fields.Selection([('draft', 'Draft'), ('raised', 'Raised'), ('sent', 'Quotation'), ('cancel', 'Cancel')], 'Sales Figure Status', default='draft', tracking=True)
    so_type = fields.Selection([('sf', 'Sales Figure'), ('so', 'Sales Order')], 'SO Type', default='so', tracking=True)
    is_mccoy = fields.Boolean('McCoy Company', default=False)
    ref = fields.Char('Ref')

    min_order = fields.Monetary('Min. Order Value')
    cancellation_window = fields.Char('Cancellation Window')
    reschedule_window = fields.Char('Reschedule Window')
    validity_quote = fields.Integer('Validity of quote')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            user_id = vals.get('user_id')
            company_id = vals.get('company_id')
            if user_id and company_id:
                user = self.env['res.users'].browse(user_id)
                company = self.env['res.company'].browse(company_id)
                if company.is_mccoy and user.user_code and user.so_sequence_id:
                    seq_date = datetime.now() + timedelta(hours=8)
                    if vals.get('date_order'):
                        seq_date = parse(str(vals['date_order'])) + timedelta(hours=8)  # fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
                    vals['ref'] = user.so_sequence_id.with_context(ir_sequence_date=seq_date).next_by_id()
        result = super(SaleOrder, self).create(vals_list)
        return result

    @api.onchange('validity_quote', 'date_order')
    def _onchange_validity_quote(self):
        if self.date_order and self.validity_quote:
            self.validity_date = self.date_order + timedelta(days=self.validity_quote)
        else:
            self.validity_date = self.date_order or datetime.now()

    @api.onchange('opportunity_id')
    def _onchange_opportunity(self):
        pricelist_obj = self.env['product.pricelist']
        if self.opportunity_id:
            pricelist = pricelist_obj.search([('currency_id', '=', self.opportunity_id.currency_id.id)], limit=1)
            if pricelist:
                self.pricelist_id = pricelist.id

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        self._onchange_opportunity()
        self.freight_terms = self.partner_id.freight_terms
        return res

    @api.onchange('company_id')
    def _onchage_company_id(self):
        self.is_mccoy = self.company_id.is_mccoy

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for so in self:
            if so.so_type == 'sf':
                so.button_sf_cancel()

        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for alert in self:
            if len(alert.order_line) == 0:
                raise UserError(_('Sorry, you cannot click confirm, Please complete the order line data first.'))

        return res

    def button_sf_raised(self):
        for so in self:
            so.sf_state = 'raised'

    def button_sf_sent(self):
        for so in self:
            so.sf_state = 'sent'

    def button_sf_cancel(self):
        for so in self:
            so.sf_state = 'cancel'

    def button_sf_draft(self):
        for so in self:
            so.sf_state = 'draft'

            if so.state == 'cancel':
                so.action_draft()

    def get_sgd_value(self, value):
        self.ensure_one()
        currency = self.currency_id
        sg_currency = self.env.ref('base.SGD')
        if currency == sg_currency:
            return value
        else:
            return currency._convert(value, sg_currency, self.company_id, self.date_order or fields.Date.today())

    def get_sgd_total_value(self, unit_price, quantity):
        limited_unit_price = round(self.get_sgd_value(unit_price), 2)
        return limited_unit_price*quantity
        
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    sale_delay = fields.Float('L/T', default=1)

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        price_unit = self.price_unit
        res = super(SaleOrderLine, self).product_uom_change()
        if price_unit > 1:
            self.price_unit = price_unit
            
        return res

    def get_min_qty(self, product):
        self.ensure_one()
        # mccoy_custom may not be installed; skip MOQ lookup if model is unavailable
        if 'mccoy.product.moq' not in self.env:
            return 1.0
        moq_obj = self.env['mccoy.product.moq']
        moq_exist = moq_obj.search([('product_variant_id', '=', product.id)], order='min_qty asc', limit=1)
        if not moq_exist:
            moq_exist = moq_obj.search([('product_id', '=', product.product_tmpl_id.id)], order='min_qty', limit=1)

        return moq_exist.min_qty or 1.0

    def _get_display_price(self, product):
        res = super(SaleOrderLine, self)._get_display_price(product)

        context = dict(self._context or {})
        company = self.order_id.company_id or self.env.company
        if company.is_mccoy and product and self.product_uom_qty and self.product_uom:
            uom = self.product_uom
            product_uom = product.uom_id.id
            if uom and uom.id != product_uom:
                uom_factor = uom._compute_price(1.0, product.uom_id)
            else:
                uom_factor = 1.0

            qty = self.product_uom_qty / uom_factor
            new_res = self.calculate_moq(product, qty)
            res = new_res and new_res / uom_factor or res

        return res

    def calculate_moq(self, product, product_uom_qty):
        self.ensure_one()
        # mccoy_custom may not be installed; skip MOQ calculation if model is unavailable
        if 'mccoy.product.moq' not in self.env:
            return 0.0
        moq_obj = self.env['mccoy.product.moq']
        moq_exist = moq_obj.search([('product_variant_id', '=', product.id), ('min_qty', '>=', product_uom_qty)], order='min_qty asc', limit=1)
        if not moq_exist:
            moq_exist = moq_obj.search([('product_variant_id', '=', product.id), ('min_qty', '<', product_uom_qty)], order='min_qty desc', limit=1)

        if not moq_exist:
            moq_exist = moq_obj.search([('product_id', '=', product.product_tmpl_id.id), ('min_qty', '>=', product_uom_qty)], order='min_qty asc', limit=1)
            if not moq_exist:
                moq_exist = moq_obj.search([('product_id', '=', product.product_tmpl_id.id), ('min_qty', '<', product_uom_qty)], order='min_qty desc', limit=1)

        return moq_exist.price_unit or 0

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        sale_delay = 1
        if self.product_id:
            customer_country = self.order_partner_id.country_id
            ###Tutup sementara, customer bilang gak pakai lagi :)
            # if customer_country:
            #     self.tax_id = customer_country.tax_ids.filtered(lambda t: t.company_id == self.env.company)

            sale_delay = self.product_id.sale_delay + 1
            if self.product_uom_qty == 1:
                self.product_uom_qty = self.get_min_qty(self.product_id)
            
        self.sale_delay = sale_delay

        return res
