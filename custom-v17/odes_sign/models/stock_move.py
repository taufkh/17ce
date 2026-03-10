# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import html2plaintext
import math
from datetime import timedelta

class StockPicking(models.Model):
    _inherit = "stock.picking"

    purchase_count = fields.Integer("purchase", compute='_compute_purchase_count')


    def _compute_purchase_count(self):

        for picking in self:
            list_purchase = []
            for move in picking.move_ids_without_package:
                if move.purchase_id.id in list_purchase:
                    continue
                else:
                    list_purchase.append(move.purchase_id.id)
            if list_purchase and list_purchase[0] == False:
                list_purchase = []
            picking.purchase_count = len(list_purchase)


    def action_view_purchase(self):
        '''
        This function returns an action that displays the opportunities from partner.
        '''
        list_purchase = []
        for picking in self:
            for move in picking.move_ids_without_package:
                if move.purchase_id.id in list_purchase:
                    continue
                else:
                    list_purchase.append(move.purchase_id.id)
            action = self.env.ref('purchase.purchase_form_action').read()[0]
            
            action['domain'] = [('id', '=', list_purchase)]
            return action

    



class StockMove(models.Model):
    _inherit = "stock.move"

    purchase_id = fields.Many2one('purchase.order',string='Purchase Order Related', copy=False)
    

