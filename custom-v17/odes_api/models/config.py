# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io
import logging
import os
import re
import random
import string
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from odoo.modules.module import get_resource_path

from random import randrange
from PIL import Image

_logger = logging.getLogger(__name__)


class Company(models.Model):
    _inherit = 'res.company'

    token_api = fields.Char("Token API")
    auth_key_notif = fields.Char("Auth Key Notifications")
    odes_database_ids = fields.One2many('odes.apps.database','company_id',"Database")


class OdesAppsDatabase(models.Model):
    _name = 'odes.apps.database'
    _description = 'ODES Apps Database'

    name = fields.Char("Name")
    domain = fields.Char("Domain")
    company_id  = fields.Many2one("res.company")
    database_name = fields.Char("Database Name")
    is_multiple_database = fields.Boolean("Multiple Database")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    token_api = fields.Char("Token API")
    auth_key_notif = fields.Char("Auth Key Notifications")
    database_config_ids = fields.One2many(related='company_id.odes_database_ids', string="Databases Configuration")


    

    def generate_token_api(self):
        letters = string.ascii_letters
        result_str = ''.join(random.choice(letters) for i in range(8))
        self.env.company.write({'token_api':result_str})
        return True


    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        apps_database_obj = self.env['odes.apps.database']
        self.env.company.write({'token_api':self.token_api})
        self.env.company.write({'auth_key_notif':self.auth_key_notif})
        # self.env.company.odes_database_ids.sudo().unlink()
        # print(self.database_ids,'awdwdwdwdwdw')
        # a+1
        # for db in self.database_ids:
        #     values = {
        #         'name':db.domain,
        #         'domain':db.domain,
        #         'company_id':self.env.company.id,
        #         'database_name':db.database_name,
        #         'is_multiple_database':db.is_multiple_database
        #     }
        #     apps = apps_database_obj.sudo().create(values)
        #     print(apps.company_id,'111111ddwdwd')
        return res


    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['token_api'] = self.env.company.token_api
        res['auth_key_notif'] = self.env.company.auth_key_notif
        # datas = []
        # if self.env.company.odes_database_ids:
        #     for db in self.env.company.odes_database_ids:
        #         values = {
        #                 'name':db.name,
        #                 'domain':db.domain,
        #                 'company_id':db.company_id.id,
        #                 'database_name':db.database_name,
        #                 'is_multiple_database':db.is_multiple_database
        #             }
        #         datas.append((0,0,values))
        #     res.update({'database_ids': datas})
        return res





class OdesAppsDatabaseSettings(models.TransientModel):
    _name = 'odes.apps.database.settings'
    _description = 'ODES Apps Database Settings'

    name = fields.Char("Name")
    domain = fields.Char("Domain")
    company_id = fields.Many2one("res.company")
    setting_id  = fields.Many2one("res.config.settings")
    database_name = fields.Char("Database Name")
    is_multiple_database = fields.Boolean("Multiple Database")



