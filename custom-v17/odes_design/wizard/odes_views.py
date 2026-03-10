# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging
import os
from tempfile import TemporaryFile

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OdesEnterpriseText(models.TransientModel):
        _name = "odes.enterprise.text"
        _description = "ODES Enterprise Text Wizard"

        name = fields.Char('Rebrand Name', required=True, default="Odes")
        website_url = fields.Char('Website Url', default="odes.com.sg")
        


        def init(self):
            # No-op on module init: legacy SQL replacement is unsafe on v16 JSON fields.
            return

        def enterprise_text(self):
            # abcd
            name = self.name
            website_url = self.website_url
            rebrand_data_obj = self.env["odes.rebrand.data"]
            rebrands = rebrand_data_obj.search([])
            
            # self._cr.execute("""update res_users SET name = REPLACE(name, 'Odoo', %s)""")
            
            if not rebrands:
                self._cr.execute("""update ir_actions SET help = REPLACE(help, 'Odoo', %s)""",(name,))
                self._cr.execute("""update ir_ui_view SET arch_db = REPLACE(arch_db, 'Odoo', %s)""",(name,))
                self._cr.execute("""update ir_ui_view SET arch_db = REPLACE(arch_db, 'odoo.com', %s)""",(website_url,))
                self._cr.execute("""update ir_ui_view SET arch_prev = REPLACE(arch_prev, 'odoo.com', %s)""",(website_url,))
                self._cr.execute("""update ir_ui_view SET arch_db = REPLACE(arch_db, 'odoo.html', 'odes.html')""")
                self._cr.execute("""update ir_ui_view SET arch_prev = REPLACE(arch_prev, 'Odoo', %s)""",(name,))
                self._cr.execute("""update ir_ui_view_custom SET arch = REPLACE(arch, 'Odoo', %s)""",(name,))
                self._cr.execute("""update ir_ui_view_custom SET arch = REPLACE(arch, 'odoo.com', %s)""",(website_url,))
                self._cr.execute("""update mail_template SET body_html = REPLACE(body_html, 'Odoo', %s)""",(name,))
                self._cr.execute("""update mail_template SET body_html = REPLACE(body_html, 'odoo.com', %s)""",(website_url,))
                self._cr.execute("""update mail_template SET subject = REPLACE(subject, 'Odoo', %s)""",(name,))
                self._cr.execute("""update mail_template SET name = REPLACE(name, 'Odoo', %s)""",(name,))
                self._cr.execute("""update mail_template SET email_from = REPLACE(email_from, 'odoo.com', %s)""",(website_url,))
                self._cr.execute("""update res_partner SET name = REPLACE(name, 'Odoo', %s)""",(name,))
                self._cr.execute("""update res_partner SET email = REPLACE(email, 'odoo', %s)""",(name,))
                self._cr.execute("""update res_partner SET website = REPLACE(website, 'odoo', %s)""",(name,))
                self._cr.execute("""update res_partner SET website = REPLACE(website, 'odoo', %s)""",(name,))
                self._cr.execute("""update ir_model_fields SET help = REPLACE(help, 'Odoo', %s)""",(name,))
                self._cr.execute("""update res_partner SET display_name = REPLACE(display_name, 'Odoo', %s)""",(name,))
                self._cr.execute("""update ir_model_fields SET field_description = REPLACE(field_description, 'Odoo', %s)""",(name,))
                self._cr.execute("""update ir_model_fields_selection SET name = REPLACE(name, 'Odoo', %s)""",(name,))
                rebrand_data_obj.create({'name' : name, 'website_url' : website_url})
            else:
                
#                ======Rebrand data contains odoo
                
                self._cr.execute("""update ir_actions SET help = REPLACE(help, 'Odoo', %s)""",(name,))
                self._cr.execute("""update ir_ui_view SET arch_db = REPLACE(arch_db, 'Odoo', %s)""",(name,))
                self._cr.execute("""update ir_ui_view SET arch_db = REPLACE(arch_db, 'odoo.com', %s)""",(website_url,))
                self._cr.execute("""update ir_ui_view SET arch_prev = REPLACE(arch_prev, 'odoo.com', %s)""",(website_url,))
                self._cr.execute("""update ir_ui_view SET arch_db = REPLACE(arch_db, 'odoo.html', 'odes.html')""")
                self._cr.execute("""update ir_ui_view SET arch_prev = REPLACE(arch_prev, 'Odoo', %s)""",(name,))
                self._cr.execute("""update ir_ui_view_custom SET arch = REPLACE(arch, 'Odoo', %s)""",(name,))
                self._cr.execute("""update ir_ui_view_custom SET arch = REPLACE(arch, 'odoo.com', %s)""",(website_url,))
                self._cr.execute("""update mail_template SET body_html = REPLACE(body_html, 'Odoo', %s)""",(name,))
                self._cr.execute("""update mail_template SET body_html = REPLACE(body_html, 'odoo.com', %s)""",(website_url,))
                self._cr.execute("""update mail_template SET subject = REPLACE(subject, 'Odoo', %s)""",(name,))
                self._cr.execute("""update mail_template SET name = REPLACE(name, 'Odoo', %s)""",(name,))
                self._cr.execute("""update mail_template SET email_from = REPLACE(email_from, 'odoo.com', %s)""",(website_url,))
                self._cr.execute("""update res_partner SET name = REPLACE(name, 'Odoo', %s)""",(name,))
                self._cr.execute("""update res_partner SET email = REPLACE(email, 'odoo', %s)""",(name,))
                self._cr.execute("""update res_partner SET website = REPLACE(website, 'odoo', %s)""",(name,))
                self._cr.execute("""update res_partner SET website = REPLACE(website, 'odoo', %s)""",(name,))
                self._cr.execute("""update ir_model_fields SET help = REPLACE(help, 'Odoo', %s)""",(name,))
                self._cr.execute("""update res_partner SET display_name = REPLACE(display_name, 'Odoo', %s)""",(name,))
                self._cr.execute("""update ir_model_fields SET field_description = REPLACE(field_description, 'Odoo', %s)""",(name,))
                self._cr.execute("""update ir_model_fields_selection SET name = REPLACE(name, 'Odoo', %s)""",(name,))
                
#                ===finish===
                
#                ====Rebrand write data based on previous rebrand
                
                self._cr.execute("""update ir_actions SET help = REPLACE(help, %s, %s)""",(rebrands.name,name))
                self._cr.execute("""update ir_ui_view SET arch_db = REPLACE(arch_db, %s, %s)""",(rebrands.name,name))
                self._cr.execute("""update ir_ui_view SET arch_db = REPLACE(arch_db, 'odoo.html', 'odes.html')""")
                
                self._cr.execute("""update ir_ui_view SET arch_db = REPLACE(arch_db, %s, %s)""",(rebrands.website_url,website_url))
                self._cr.execute("""update ir_ui_view SET arch_prev = REPLACE(arch_prev, %s, %s)""",(rebrands.website_url,website_url))
                self._cr.execute("""update ir_ui_view SET arch_prev = REPLACE(arch_prev, %s, %s)""",(rebrands.name,name))
                self._cr.execute("""update ir_ui_view_custom SET arch = REPLACE(arch, %s, %s)""",(rebrands.name,name))
                self._cr.execute("""update ir_ui_view_custom SET arch = REPLACE(arch, %s, %s)""",(rebrands.website_url,website_url))
                self._cr.execute("""update mail_template SET body_html = REPLACE(body_html, %s, %s)""",(rebrands.name,name))
                self._cr.execute("""update mail_template SET body_html = REPLACE(body_html, %s, %s)""",(rebrands.website_url,website_url))
                self._cr.execute("""update mail_template SET subject = REPLACE(subject, %s, %s)""",(rebrands.name,name))
                self._cr.execute("""update mail_template SET name = REPLACE(name, %s, %s)""",(rebrands.name,name))
                self._cr.execute("""update mail_template SET email_from = REPLACE(email_from, %s, %s)""",(rebrands.website_url,website_url))
                self._cr.execute("""update res_partner SET name = REPLACE(name, %s, %s)""",(rebrands.name,name))
                self._cr.execute("""update res_partner SET email = REPLACE(email, %s, %s)""",(rebrands.name,name))
                self._cr.execute("""update res_partner SET website = REPLACE(website, %s, %s)""",(rebrands.name,name))
                self._cr.execute("""update res_partner SET website = REPLACE(website, %s, %s)""",(rebrands.name,name))
                self._cr.execute("""update res_partner SET display_name = REPLACE(display_name, %s, %s)""",(rebrands.name,name))
                self._cr.execute("""update ir_model_fields SET help = REPLACE(help, %s, %s)""",(rebrands.name,name))
                self._cr.execute("""update ir_model_fields SET field_description = REPLACE(field_description, %s, %s)""",(rebrands.name,name))
                self._cr.execute("""update ir_model_fields_selection SET name = REPLACE(name, %s, %s)""",(rebrands.name,name))
                rebrands.write({'name' : name, 'website_url' : website_url})
            
            
            return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
            }
