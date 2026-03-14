from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_split_select = fields.Boolean(string='Select Product')
    order_state = fields.Selection(related='order_id.state', readonly=True)

    def action_toggle_split_select(self):
        for line in self:
            line.x_split_select = not line.x_split_select
        return True
