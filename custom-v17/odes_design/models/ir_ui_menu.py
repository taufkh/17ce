# -*- coding: utf-8 -*-
# Copyright 2015 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class IrUiMenuCategory(models.Model):
    _name = 'odes.ir.ui.menu.category'
    _description = 'Menu Category'


    name = fields.Char(
        string='Category name',
    )
    
    menu_line_ids = fields.One2many('ir.ui.menu', 'category_menu_id', 'Menu List', copy=True)

class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    category_menu_id = fields.Many2one(
        'odes.ir.ui.menu.category', 'Category',
        help="Category of the menu.")
    

