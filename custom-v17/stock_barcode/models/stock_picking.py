from odoo import _, api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _get_client_action(self, picking_id):
        """Community fallback for barcode controller callers."""
        view_id = self.env.ref('stock.view_picking_form').id
        return {
            'name': _('Barcode Picking'),
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': picking_id,
        }

