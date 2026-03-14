# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    moq_qty = fields.Float(string='Minimum Order Quantity')
    spq_qty = fields.Float(string='Standard Packaging Quantity')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _check_moq_spq(self):
        for order in self:
            for line in order.order_line:
                supplier_info = line.product_id.seller_ids.filtered(
                    lambda s: s.partner_id == order.partner_id and s.product_uom == line.product_uom and s.currency_id == order.currency_id
                )
                if supplier_info:
                    supplier_info = supplier_info[0]
                    moq = supplier_info.moq_qty
                    spq = supplier_info.spq_qty
                    if moq and line.product_qty < moq:
                        raise ValidationError(
                            f"The quantity for {line.product_id.name} is below the Minimum Order Quantity of {moq}."
                        )
                    if spq and (line.product_qty % spq) != 0:
                        raise ValidationError(
                            f"The quantity for {line.product_id.name} must be a multiple of the Standard Packaging Quantity of {spq}."
                        )

    def button_confirm(self):
        self._check_moq_spq()
        return super().button_confirm()
