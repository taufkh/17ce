from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    split_from_id = fields.Many2one(
        'sale.order',
        string='Split From',
        copy=False,
    )
    extracted_from_id = fields.Many2one(
        'sale.order',
        string='Extracted From',
        copy=False,
    )
    split_child_ids = fields.One2many(
        'sale.order',
        'split_from_id',
        string='Splited Quotations',
    )
    extracted_child_ids = fields.One2many(
        'sale.order',
        'extracted_from_id',
        string='Extracted Quotations',
    )
    split_count = fields.Integer(compute='_compute_split_counts')
    extracted_count = fields.Integer(compute='_compute_split_counts')

    @api.depends('split_child_ids', 'extracted_child_ids')
    def _compute_split_counts(self):
        for order in self:
            order.split_count = len(order.split_child_ids)
            order.extracted_count = len(order.extracted_child_ids)

    def action_toggle_all_split_lines(self, value):
        for order in self:
            if order.state != 'draft':
                continue
            lines = order.order_line.filtered(lambda l: not l.display_type)
            lines.write({'x_split_select': value})
        return True

    def action_select_all_split_lines(self):
        return self.action_toggle_all_split_lines(True)

    def action_unselect_all_split_lines(self):
        return self.action_toggle_all_split_lines(False)

    def action_open_split_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Split Quote'),
            'res_model': 'sale.order.split.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'default_order_id': self.id,
                'default_mode': 'split',
            },
        }

    def action_open_extract_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Extract Quote'),
            'res_model': 'sale.order.split.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'default_order_id': self.id,
                'default_mode': 'extract',
            },
        }

    def action_view_split_children(self):
        self.ensure_one()
        action = self.env.ref('sale.action_quotations').read()[0]
        action['domain'] = [('split_from_id', '=', self.id)]
        action['context'] = dict(self._context, default_split_from_id=self.id)
        return action

    def action_view_extracted_children(self):
        self.ensure_one()
        action = self.env.ref('sale.action_quotations').read()[0]
        action['domain'] = [('extracted_from_id', '=', self.id)]
        action['context'] = dict(self._context, default_extracted_from_id=self.id)
        return action
