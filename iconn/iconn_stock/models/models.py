# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    required_attachment = fields.Binary(string="Required Document", copy=False, attachment=True)
    required_attachment_filename = fields.Char(string="Required Document Filename", copy=False, tracking=True)
    packing_note = fields.Text(string="Packing List Notes", copy=False, tracking=True)
    source_type = fields.Selection([
        ('po', 'From Purchase Order'),
        ('return', 'Customer Return'),
        ('internal', 'Internal Transfer'),
        ('other', 'Other')
        ], string="Source Type", readonly=True, copy=False, tracking=True, compute='_compute_source_type', store=True)

    def button_validate(self):
        for rec in self:
            if rec.picking_type_code == 'outgoing' and not rec.required_attachment:
                raise ValidationError("Cannot validate Delivery Order: Required Document is missing.")
        res = super().button_validate()
        return res
    
    @api.depends('purchase_id', 'picking_type_id')
    def _compute_source_type(self):
        for rec in self:
            source_type = 'other'
            if rec.picking_type_code == 'incoming':
                if rec.purchase_id:
                    source_type = 'po'
                elif rec.move_ids_without_package.mapped('sale_line_id'):
                    source_type = 'return'
            elif rec.picking_type_code == 'internal':
                source_type = 'internal'
            elif rec.picking_type_code == 'outgoing':
                source_type = False
            rec.source_type = source_type
