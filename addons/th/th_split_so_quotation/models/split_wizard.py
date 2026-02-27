from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrderSplitWizard(models.TransientModel):
    _name = 'sale.order.split.wizard'
    _description = 'Split / Extract Quotation Wizard'

    order_id = fields.Many2one('sale.order', string='Quotation', required=True)
    mode = fields.Selection(
        [('split', 'Split'), ('extract', 'Extract')],
        default='split',
        required=True,
    )
    line_ids = fields.One2many('sale.order.split.wizard.line', 'wizard_id', string='Lines')

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        order = None
        if defaults.get('order_id'):
            order = self.env['sale.order'].browse(defaults['order_id'])
        elif self.env.context.get('active_id'):
            order = self.env['sale.order'].browse(self.env.context['active_id'])
        if not order:
            return defaults
        lines = order.order_line.filtered(lambda l: not l.display_type)
        selected = lines.filtered(lambda l: l.x_split_select)
        target_lines = selected or lines
        defaults['line_ids'] = [
            (0, 0, {
                'order_line_id': line.id,
                'product_id': line.product_id.id,
                'quantity': line.product_uom_qty,
                'uom_id': line.product_uom.id,
            })
            for line in target_lines
        ]
        defaults['order_id'] = order.id
        return defaults

    def _validate_quantities(self):
        for wizard in self:
            for line in wizard.line_ids:
                if line.quantity <= 0:
                    raise ValidationError(_('Quantity must be greater than 0.'))
                if line.order_line_id and line.quantity > line.order_line_id.product_uom_qty:
                    raise ValidationError(
                        _('Split quantity cannot exceed the original line quantity.')
                    )

    def _create_new_quotation(self):
        self.ensure_one()
        order = self.order_id
        new_order = order.copy(default={'order_line': False, 'name': '/'})
        if not new_order.name or new_order.name == '/':
            seq = self.env['ir.sequence'].with_company(new_order.company_id).next_by_code('sale.order')
            new_order.name = seq or '/'
        return new_order

    def _copy_line_to_order(self, new_order, wizard_line):
        order_line = wizard_line.order_line_id
        if order_line:
            vals = order_line.copy_data()[0]
            vals.update({
                'order_id': new_order.id,
                'product_uom_qty': wizard_line.quantity,
                'x_split_select': False,
            })
            self.env['sale.order.line'].create(vals)
            return
        if not wizard_line.product_id:
            return
        self.env['sale.order.line'].create({
            'order_id': new_order.id,
            'product_id': wizard_line.product_id.id,
            'product_uom_qty': wizard_line.quantity,
            'product_uom': wizard_line.uom_id.id,
            'name': wizard_line.product_id.display_name,
            'x_split_select': False,
        })

    def _apply_split_on_original(self, wizard_line, remove_qty):
        if not remove_qty:
            return
        order_line = wizard_line.order_line_id
        if not order_line:
            return
        remaining = order_line.product_uom_qty - wizard_line.quantity
        if remaining <= 0:
            order_line.unlink()
        else:
            order_line.write({'product_uom_qty': remaining})

    def action_confirm(self):
        self.ensure_one()
        self._validate_quantities()

        order = self.order_id
        remove_qty = bool(self.env['ir.config_parameter'].sudo().get_param(
            'th_split_so_quotation.remove_split_qty', default='False'
        ) == 'True')

        new_order = self._create_new_quotation()
        if self.mode == 'split':
            new_order.split_from_id = order.id
        else:
            new_order.extracted_from_id = order.id

        for wizard_line in self.line_ids:
            self._copy_line_to_order(new_order, wizard_line)
            if self.mode == 'split':
                self._apply_split_on_original(wizard_line, remove_qty)

        order.order_line.write({'x_split_select': False})

        action = self.env.ref('sale.action_quotations').read()[0]
        action['res_id'] = new_order.id
        action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
        action['view_mode'] = 'form'
        return action


class SaleOrderSplitWizardLine(models.TransientModel):
    _name = 'sale.order.split.wizard.line'
    _description = 'Split / Extract Quotation Line'

    wizard_id = fields.Many2one('sale.order.split.wizard', required=True, ondelete='cascade')
    order_line_id = fields.Many2one('sale.order.line', string='Order Line')
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    quantity = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True)
