from odoo import api, fields, models, _


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    quotation_line_ids = fields.One2many(
        'crm.quotation.line',
        'lead_id',
        string='Quotation Lines',
    )
    x_quotation_outcome = fields.Selection(
        [
            ('won', 'Won'),
            ('partial', 'Partial Won'),
        ],
        string='Quotation Outcome',
        compute='_compute_quotation_outcome',
        store=True,
        readonly=True,
    )

    @api.depends('stage_id', 'quotation_line_ids.state')
    def _compute_quotation_outcome(self):
        for lead in self:
            if not lead.stage_id or not lead.stage_id.is_won:
                lead.x_quotation_outcome = False
                continue
            lines = lead.quotation_line_ids
            if not lines:
                lead.x_quotation_outcome = 'won'
                continue
            won_count = len(lines.filtered(lambda l: l.state == 'won'))
            if won_count and won_count < len(lines):
                lead.x_quotation_outcome = 'partial'
            else:
                lead.x_quotation_outcome = 'won'

    def action_set_lost(self, **additional_values):
        res = super().action_set_lost(**additional_values)
        for lead in self:
            if lead.quotation_line_ids:
                values = {'state': 'lost'}
                if lead.lost_reason_id:
                    values['lost_reason_id'] = lead.lost_reason_id.id
                lead.quotation_line_ids.write(values)
        return res

    def action_select_all_quotation_lines(self):
        for lead in self:
            lead.quotation_line_ids.write({'select_line': True})
        return True

    def action_clear_all_quotation_lines(self):
        for lead in self:
            lead.quotation_line_ids.write({'select_line': False})
        return True

    def action_sale_quotations_new(self):
        self.ensure_one()
        selected_lines = self.quotation_line_ids.filtered(lambda l: l.select_line)
        if not selected_lines or not self.partner_id:
            return super().action_sale_quotations_new()

        action = super().action_sale_quotations_new()
        ctx = dict(action.get('context', {}))
        vals = {k[8:]: v for k, v in ctx.items() if k.startswith('default_')}
        vals.setdefault('partner_id', self.partner_id.id)
        if self.company_id:
            vals.setdefault('company_id', self.company_id.id)
        if 'opportunity_id' in self.env['sale.order']._fields:
            vals.setdefault('opportunity_id', self.id)

        order_new = self.env['sale.order'].with_context(ctx).new(vals)
        if hasattr(order_new, '_onchange_partner_id'):
            order_new._onchange_partner_id()
        vals = order_new._convert_to_write(order_new._cache)
        order = self.env['sale.order'].with_context(ctx).create(vals)

        for line in selected_lines:
            product = line.product_id
            if not product:
                continue
            name = product.get_product_multiline_description_sale() if hasattr(
                product, 'get_product_multiline_description_sale'
            ) else product.display_name
            self.env['sale.order.line'].create({
                'order_id': order.id,
                'product_id': product.id,
                'product_uom_qty': 1,
                'product_uom': product.uom_id.id,
                'price_unit': line.quoted_price or 0.0,
                'name': name,
            })
            line.sale_order_id = order.id
            line.select_line = False

        action.update({
            'res_id': order.id,
            'views': [(self.env.ref('sale.view_order_form').id, 'form')],
            'view_mode': 'form',
        })
        return action
