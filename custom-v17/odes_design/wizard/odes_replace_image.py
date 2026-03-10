# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging
import os
from tempfile import TemporaryFile

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OdesReplaceImage(models.TransientModel):
        _name = "odes.replace.image"
        _description = "ODES Replace Image Wizard"

        name = fields.Char('Replace Image')
        


        def init(self):
            # No-op on module init: avoid broad SQL mutations during install.
            return

        def enterprise_image(self):
            # abcd
            
            menu_obj = self.env["ir.ui.menu"]
            menus = menu_obj.search([('parent_id', '=', False)])
            menu_nam = [x.name for x in menus]
            
            for menu in menus:
                name_image = menu.name.replace(" ", "-")
                name_full = 'odes_design,static/description/'+name_image+'.png'
                menu.write({'web_icon' : name_full})
                print (name_full)
            print (len(menus), 'fff')
            print (menu_nam, 'ddsd')
            self._cr.execute("""update ir_ui_view SET arch_db = REPLACE(arch_db, '/web/static/src/img/odoo_logo_tiny.png', '/odes_design/static/src/img/odes_logo_tiny.png')""")
            return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
            }
